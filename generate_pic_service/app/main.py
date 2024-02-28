import os
from fastapi import FastAPI
from pydantic import BaseModel
import logging
import json
import time
from fastapi.responses import Response
import pybase64
import requests
import redis
import asyncpg
import chardet
import pika
import ast
import aio_pika
import asyncio
import psycopg2
from fastapi.middleware.cors import CORSMiddleware



class Text(BaseModel):
    id: int
    description: str
    

class Text2ImageAPI:

    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=1024, height=1024):
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }

        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']

            attempts -= 1
            time.sleep(delay)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Укажите здесь домены, разрешенные для запросов, или "*", чтобы разрешить все домены
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Укажите методы, разрешенные для запросов
    allow_headers=["*"],  # Укажите здесь заголовки, разрешенные для запросов, или "*", чтобы разрешить все заголовки
)

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
rabbit_host = os.environ.get("RABBIT_HOST")
redis_host = os.environ.get("REDIS_HOST")


r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
logging.warning(r)


async def update_db(images, id):
    conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
    row = await conn.execute(f'UPDATE texts SET pic = $1 WHERE id=$2', images[0], id)
    await conn.close()
    
def sync_update_db(images, id):
    conn = psycopg2.connect(user=db_user, password=db_password, dbname=db_name, host=db_host)
    cursor = conn.cursor()
    cursor.execute('UPDATE texts SET pic = %s WHERE id=%s', (images[0], id))
    conn.commit()
    cursor.close()
    conn.close()

@app.get('/generate_pic')
async def async_generate_pic(id:int, description: str):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '5BE53FCEB1AE2634CCC69B87CD015EE7', '3E12646F716819AD9BE4515B752C29BD')
    model_id = api.get_model()
    uuid = api.generate(description, model_id)
    images = api.check_generation(uuid)
    logging.warning(type(images[0]))
    detected_encoding = chardet.detect(images[0].encode())
    detected_encoding_name = detected_encoding['encoding']
    logging.warning(detected_encoding_name)
    
    r.set(id, images[0])
    update_db(images, id)
    
    image = pybase64.b64decode(images[0])
    
    return Response(content=image, media_type='image/png')


@app.get('/see_pic')
async def get_pic_from_redis(id: int):
    image = pybase64.b64decode(r.get(id))
    return Response(content=image, media_type='image/png')


def generate_pic(id:int, description: str):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '5BE53FCEB1AE2634CCC69B87CD015EE7', '3E12646F716819AD9BE4515B752C29BD')
    model_id = api.get_model()
    uuid = api.generate(description, model_id)
    images = api.check_generation(uuid)
    logging.warning(type(images[0]))
    detected_encoding = chardet.detect(images[0].encode())
    detected_encoding_name = detected_encoding['encoding']
    logging.warning(detected_encoding_name)
    
    redis_value = r.get(id)
    if redis_value is None:
        r.set(id, images[0])
    else:
        r.set(id, images[0], xx=True)
    sync_update_db(images, id)
    
    image = pybase64.b64decode(images[0])
    
    return Response(content=image, media_type='image/png')

def callback(ch, method, properties, body):
    logging.warning('Message received, callback!')
    received_text = ast.literal_eval(body.decode('utf-8'))
    logging.warning(received_text)
    generate_pic(**received_text)
    

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))
logging.warning(connection)
channel = connection.channel()
channel.queue_declare(queue='generate_pic')
channel.basic_consume(on_message_callback=callback, queue='generate_pic', auto_ack=True)
channel.start_consuming()


# async def consume_messages():
#     connection = await aio_pika.connect_robust(host=rabbit_host)
#     async with connection:
#         channel = await connection.channel()
#         queue = await channel.declare_queue("generate_pic", durable=True)
        
#         async for message in queue:
#             async with message.process():
#                 print("Received message:", message.body.decode())
                
# @app.on_event("startup")
# async def startup_event():
#     asyncio.create_task(consume_messages())