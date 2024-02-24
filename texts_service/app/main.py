import os
from fastapi import FastAPI
from pydantic import BaseModel
import logging
from fastapi.responses import JSONResponse
from uuid import uuid4
import pybase64
import asyncpg
import redis
import requests

app = FastAPI()

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
url = os.environ.get("API_URL")
rabbit_host = os.environ.get("RABBIT_HOST")
redis_host = os.environ.get("REDIS_HOST")

class Text(BaseModel):
    title: str = None
    description: str = None
    fanfic_text: str = None
    

async def create_table(conn):
    query = '''CREATE TABLE IF NOT EXISTS texts (
    id SERIAL PRIMARY KEY,
    title TEXT,
    description TEXT,
    fanfic_text TEXT,
    pic TEXT
    );'''
    await conn.execute(query)


@app.post('/create_text')
async def create_text(data: Text):
    try:
        logging.warning(data)
        conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
        created = await create_table(conn)
        logging.warning(created)
        row = await conn.fetchrow(f'INSERT INTO texts (title, description, fanfic_text) VALUES ($1, $2, $3) RETURNING id', data.title, data.description, data.fanfic_text)
        logging.warning(row)
        inserted_id = row['id']
        await conn.close()
        result = requests.get(f'{url}/generate_pic', params={'id': inserted_id, 'prompt': data.description})
        logging.warning(result)
        return inserted_id
    except Exception as e:
        logging.error(e, exc_info=True)
    

r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
logging.warning(r)

@app.get('/get_text/{id}')
async def get_text(id: int):
    try:
        check = r.get(id)
        logging.warning(f'Value from redis: {check}')
        if check is None:
            conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
            row = await conn.fetchrow(f'SELECT * FROM texts WHERE id = $1', id)
            await conn.close()
        else:
            conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
            row = await conn.fetchrow(f'SELECT title, description, fanfic_text FROM texts WHERE id = $1', id)
            await conn.close()
            row = dict(row)
            row['pic'] = check
        return row
    except Exception as e:
        logging.error(e, exc_info=True)

@app.put('/edit_text/{id}')
async def edit_text(data: Text, id: int):
    try:
        conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
        if data.title is not None:
            update = await conn.execute(f'''
                UPDATE texts
                SET title = $1
                WHERE id= $2''', data.title, id)
        if data.description is not None:
            update = await conn.execute(f'''
                UPDATE texts
                SET description = $1
                WHERE id=$2''', data.description, id)
        if data.fanfic_text is not None:
            update = await conn.execute(f'''
                UPDATE texts
                SET fanfic_text = $1
                WHERE id=$2''', data.fanfic_text, id)
        await conn.close()
    except Exception as e:
        logging.error(e, exc_info=True)
        
@app.put('/generate_pic')
async def generate_pic(id: int, description: str):
    return None


@app.delete('/delete_text')
async def delete_text(id: int):
    try:
        conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
        row = await conn.execute(f'DELETE FROM texts WHERE id = $1 RETURNING id', id)
        await conn.close()
        return row
    except Exception as e:
        logging.error(e, exc_info=True)
        