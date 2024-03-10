import base64
import csv
import json
import threading
import time
import uuid

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi import BackgroundTasks
import boto3
import asyncio

app = FastAPI()
origins = ["*"]
REQUEST_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/339712806862/1225316534-req-queue"
RESPONSE_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/339712806862/1225316534-resp-queue"
REGION = 'us-east-1'
APP_TIER_INSTANCE = "app-tier-instance-"
sqs = boto3.client('sqs',region_name ='us-east-1')
ec2 = boto3.client('ec2',region_name ='us-east-1')

role_arn = "arn:aws:iam::339712806862:role/web-tier-role"

results_map = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def startup():
    thread1 = threading.Thread(target=autoscaling_controller)
    thread2 = threading.Thread(target=results_mapper)

    thread1.start()
    thread2.start()


def results_mapper():
    sqs_resources = boto3.resource('sqs',region_name=REGION)
    while True:
        queue = sqs_resources.Queue(RESPONSE_QUEUE_URL)
        responseCount = int(queue.attributes['ApproximateNumberOfMessages'])
        
        if responseCount == 0:
            time.sleep(1)
            continue

        response = sqs.receive_message(
            QueueUrl=RESPONSE_QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=1
        )

        messages = response.get('Messages',None)

        if messages:
            for message in messages:
                body = message['Body']
                bodyObject = json.loads(body)
                
                if bodyObject['request_id'] in results_map:
                    results_map[bodyObject['request_id']] = bodyObject['result']
                
                sqs.delete_message(
                    QueueUrl = RESPONSE_QUEUE_URL,
                    ReceiptHandle = message['ReceiptHandle']
                )
        time.sleep(1)
            


def autoscaling_controller():

    ec2_resources = boto3.resource('ec2',region_name=REGION)
    sqs_resources = boto3.resource('sqs',region_name=REGION)

    while True:
        queue = sqs_resources.Queue(REQUEST_QUEUE_URL)
        requestCount = int(queue.attributes['ApproximateNumberOfMessages'])

        if requestCount == 0:
            time.sleep(5)
            continue
            
        instances = ec2_resources.instances.all()
        stopped_instances = []

        for instance in instances:
            if instance.state['Name'] == 'stopped':
                stopped_instances.append(instance)
            
        sorted_stopped_instances = sorted(stopped_instances, key=lambda instance: [tag['Value'] for tag in instance.tags if tag['Key'] == 'Name'][0] if any(tag['Key'] == 'Name' for tag in instance.tags) else '')
        print(sorted_stopped_instances)
        stoppedInstanceCount = len(sorted_stopped_instances) 

        print(stoppedInstanceCount)

        numberOfInstanceToBeStarted = min(10,stoppedInstanceCount)    
        
        if numberOfInstanceToBeStarted > 0 :
            instances_to_start = sorted_stopped_instances[0:numberOfInstanceToBeStarted]
        
            for instance in instances_to_start:
                instance.start()
                print(f'Starting instance {instance.id}')
                        
        time.sleep(180)
        

@app.on_event("startup")
async def startup_event():
    startup()


@app.get("/check", tags=["Root"])
async def read_root():
    return {"hello": "hello"}


@app.post("/", tags=["Root"], response_class=PlainTextResponse)
async def read_root(inputFile: UploadFile = File(...)):
    file_contents = await inputFile.read()

    encoded_contents = base64.b64encode(file_contents)

    encoded_string = encoded_contents.decode('utf-8')
    request_id = str(uuid.uuid4())
    

    message_object = json.dumps({ "request_id":request_id, "encoded_image": encoded_string,"name":inputFile.filename})

    q_response = sqs.send_message(QueueUrl = REQUEST_QUEUE_URL,MessageBody=message_object)
    

    print(q_response)

    results_map[request_id] = None

    while results_map[request_id] == None:
        await asyncio.sleep(0.5)

    response_string = f"{inputFile.filename.split('.')[0]}:{results_map[request_id]}"
    
    print(response_string)

    results_map.pop(request_id)
    return response_string
