import csv

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi import BackgroundTasks
import boto3

app = FastAPI()
origins = ["*"]
request_queue_url = "https://sqs.us-east-1.amazonaws.com/339712806862/1225316534-req-queue"

sqs = boto3.client('sqs',region_name = 'us-east-1')

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_results = {}


async def load_classification_results():
    with open('./data/classification_results.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            image_results[row[0]] = row[1]

async def autoscaling_controller():
    ec2_resources = boto3.resource('ec2')
    
    while True:
        instances = ec2_resources.instances
        count = len(list(instances))

        response = sqs.send_message(QueueUrl=request_queue_url,MessageBody=str(count))
        print(response)
        # response = ec2_client.describe_instances()
        
        

# Load classification results asynchronously during startup
@app.on_event("startup")
async def startup_event(background_tasks:BackgroundTasks):
    return 


@app.get("/check", tags=["Root"])
async def read_root():
    return {"hello": "hello"}


@app.post("/", tags=["Root"], response_class=PlainTextResponse)
async def read_root(inputFile: UploadFile = File(...)):
    filename = inputFile.filename.split(".")[0]
    result = image_results.get(filename, "Unknown")
    return f"{filename}:{result}"
