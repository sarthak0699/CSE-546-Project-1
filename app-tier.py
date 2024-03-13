import asyncio
import base64
import io
import json
import subprocess
import boto3
import requests

request_queue_url = "https://sqs.us-east-1.amazonaws.com/339712806862/1225316534-req-queue"
response_queue_url = "https://sqs.us-east-1.amazonaws.com/339712806862/1225316534-resp-queue"


sqs = boto3.client('sqs', region_name='us-east-1')
ec2 = boto3.client('ec2', region_name='us-east-1')
s3 = boto3.client('s3',  region_name = 'us-east-1')

IN_BUCKET = '1225316534-in-bucket'
OUT_BUCKET = '1225316534-out-bucket'
ENCODED_IMAGE = 'encoded_image'
FILE_NAME = 'request_image.jpg'
def decode_base64_to_image(encoded_string, output_filename):
    # Decode the base64-encoded string to bytes
    decoded_bytes = base64.b64decode(encoded_string)

    # Write the bytes to an image file
    with open(output_filename, 'wb') as f:
        f.write(decoded_bytes)


def run_image_recognition():
    proc = subprocess.Popen(['python3', 'face_recognition.py',  FILE_NAME], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = proc.communicate()[0].decode('utf-8').strip()
    return result

# encoded_string = "your_base64_encoded_string_here"
  
async def poll_queue():
    count = 0
    print("Polling started")
    while True:
        response = sqs.receive_message(
            QueueUrl=request_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=0
        )
        print(count)
        message = response.get('Messages', None)
        if message:
            count = 0
            body = message[0]['Body']
            bodyObject = json.loads(body)
            decode_base64_to_image(bodyObject[ENCODED_IMAGE],FILE_NAME)
            result = run_image_recognition()
            sqs.delete_message(
                QueueUrl=request_queue_url,
                ReceiptHandle=message[0]['ReceiptHandle']
            )
            print("HERE")
            message_object = json.dumps({ "request_id":bodyObject['request_id'], "result": result})

            q_response = sqs.send_message(QueueUrl = response_queue_url,MessageBody=message_object)


            print(q_response)
            decoded_bytes = base64.b64decode(bodyObject[ENCODED_IMAGE])

            name = bodyObject['name']

            s3_in_response = s3.put_object(Body = decoded_bytes,Bucket = IN_BUCKET,Key=name)
            print(s3_in_response)

            name = name.split('.')[0]
            s3_out_response = s3.put_object(Body = result,Bucket = OUT_BUCKET,Key=name)
            print(s3_out_response)



        else:
            count += 1
        
        if count == 30:
            instance_id = requests.get("http://169.254.169.254/latest/meta-data/instance-id").text
            response = ec2.stop_instances(InstanceIds=[instance_id])
            print(response)


        await asyncio.sleep(1)

asyncio.run(poll_queue())
