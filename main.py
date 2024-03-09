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
request_queue_url = "https://sqs.us-east-1.amazonaws.com/339712806862/1225316534-req-queue"
region = 'us-east-1'

# sqs = boto3.client('sqs',region_name ='us-east-1')

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

    ec2_resources = boto3.resource('ec2',region_name=region)
    sqs_resources = boto3.resource('sqs',region_name=region)

    while True:
        instances = ec2_resources.instances.all()
        instanceCount = len(list(instances)) - 1

        queue = sqs_resources.Queue(request_queue_url)
        requestCount = queue.attributes['ApproximateNumberOfMessages']
        
        print(instanceCount)
        print(requestCount)
                
        await asyncio.sleep(10)
        

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

    q_response = sqs.send_message(QueueUrl = request_queue_url,MessageBody=message_object)
    

    return f"${q_response}"
