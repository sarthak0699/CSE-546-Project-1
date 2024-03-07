import base64
import csv
import time

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi import BackgroundTasks
import boto3
import asyncio

app = FastAPI()
origins = ["*"]
request_queue_url = "https://sqs.us-east-1.amazonaws.com/339712806862/1225316534-req-queue"

sqs = boto3.client('sqs',region_name ='us-east-1')

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
    ec2_resources = boto3.resource('ec2',region_name='us-east-1')
    
    while True:
        instances = ec2_resources.instances.all()
        
        count = len(list(instances)) - 1
        print(count)        
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

    return f"bruh"
