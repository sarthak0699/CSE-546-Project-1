import csv
import asyncio
from typing import Optional

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

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


async def load_classification_results():
    with open('./data/classification_results.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        for row in reader:
            image_results[row[0]] = row[1]


# Load classification results asynchronously during startup
@app.on_event("startup")
async def startup_event():
    await load_classification_results()


@app.get("/check", tags=["Root"])
async def read_root():
    return {"hello": "hello"}


@app.post("/", tags=["Root"], response_class=PlainTextResponse)
async def read_root(inputFile: UploadFile = File(...)):
    filename = inputFile.filename.split(".")[0]
    result = image_results.get(filename, "Unknown")
    return f"{filename}: {result}"
