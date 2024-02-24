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

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
rabbit_host = os.environ.get("RABBIT_HOST")
redis_host = os.environ.get("REDIS_HOST")


r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
logging.warning(r)


@app.get('/generate_pic')
async def generate_pic(id:int, prompt: str):
    api = Text2ImageAPI('https://api-key.fusionbrain.ai/', '5BE53FCEB1AE2634CCC69B87CD015EE7', '3E12646F716819AD9BE4515B752C29BD')
    model_id = api.get_model()
    uuid = api.generate(prompt, model_id)
    images = api.check_generation(uuid)
    logging.warning(type(images[0]))
    detected_encoding = chardet.detect(images[0].encode())
    detected_encoding_name = detected_encoding['encoding']
    logging.warning(detected_encoding_name)
    
    image = pybase64.b64decode(images[0])
    
    r.set(id, images[0])
    
    conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
    row = await conn.execute(f'UPDATE texts SET pic = $1 WHERE id=$2', images[0], id)
    await conn.close()
    
    return Response(content=image, media_type='image/png')

@app.get('/see_pic')
async def get_pic_from_redis(id: int):
    image = pybase64.b64decode(r.get(id))
    return Response(content=image, media_type='image/png')