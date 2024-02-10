
import csv
from typing import Optional

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

image_results = {}

with open('./data/classification_results.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        image_results[row[0]] = row[1]
        

@app.get("/check", tags=["Root"])
async def read_root():
    # result = image_results[image.filename.split(".")[0]]
    return {"hello":"hello"}

@app.post("/", tags=["Root"],response_class=PlainTextResponse)
async def read_root(inputFile:UploadFile = File(...)):
    result = image_results[inputFile.filename.split(".")[0]]
    return inputFile.filename.split(".")[0] +":" + result

