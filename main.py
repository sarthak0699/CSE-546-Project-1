import base64
import csv
import json
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
REGION = 'us-east-1'
APP_TIER_INSTANCE = "app-tier-instance-"
sqs = boto3.client('sqs',region_name ='us-east-1')
ec2 = boto3.client('ec2',region_name ='us-east-1')

role_arn = "arn:aws:iam::339712806862:role/web-tier-role"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def startup():
    asyncio.create_task(autoscaling_controller())

async def autoscaling_controller():

    ec2_resources = boto3.resource('ec2',region_name=REGION)
    sqs_resources = boto3.resource('sqs',region_name=REGION)

    while True:
        queue = sqs_resources.Queue(REQUEST_QUEUE_URL)
        requestCount = queue.attributes['ApproximateNumberOfMessages']

        if requestCount == 0:
            await asyncio.sleep(5)
            
        instances = ec2_resources.instances.all()
        stopped_instances_id = []

        for instance in instances:
            if instance.state['Name'] == 'stopped':
                stopped_instances_id.append(instance.id)
            


        stoppedInstanceCount = len(stopped_instances_id) 

        print(stoppedInstanceCount)

        
        numberOfInstanceToBeCreated = min(requestCount,20-stoppedInstanceCount)    

        print(numberOfInstanceToBeCreated)

        
                
        await asyncio.sleep(5)
        

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
    

    message_object = json.dumps({ "request_id":request_id, "encoded_image": encoded_string})

    q_response = sqs.send_message(QueueUrl = REQUEST_QUEUE_URL,MessageBody=message_object)
    

    return f"${q_response}"
