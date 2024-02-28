import os
import logging
import asyncio
import asyncpg
import ast
from fastapi import FastAPI, HTTPException
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.gigachat import GigaChat
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import aiormq
import uvicorn
import pika

app = FastAPI()

async def callback(ch, method, properties, body):
    logging.warning('Message received, callback!')
    received_text = ast.literal_eval(body.decode('utf-8'))
    logging.warning(received_text)
    chat_request = ChatRequest(text=received_text['fanfic_text'], text_id=received_text['id'])
    await generate_tags(request=chat_request)

db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
logging.warning('RABBIT_HOST')
rabbit_host = os.environ.get("RABBIT_HOST")

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))
logging.warning(connection)
channel = connection.channel()
channel.queue_declare(queue='generate_tags')
channel.basic_consume(on_message_callback=callback, queue='generate_tags', auto_ack=True)
channel.start_consuming()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Авторизация в сервисе GigaChat
gigachat_credentials = "ZTkwNzU5MmQtYjk0NC00OWQ2LWFlZDItMzcyYzE5MDNkODYyOjdhNzY4NWM1LWZlMDEtNGMyMC04ZjVlLTE3MmU3NGFhNzY5Ng=="
gigachat_chat = GigaChat(credentials=gigachat_credentials, verify_ssl_certs=False)


class ChatRequest(BaseModel):
    text: str
    text_id: int


async def update_database_with_tags(text_id, tags):
    conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
    await conn.execute('UPDATE texts SET tags = $1 WHERE id = $2', tags, text_id)
    await conn.close()


@app.post("/generate_tags")
async def generate_tags(request: ChatRequest):
    try:
        # Формирование сообщений для чата
        prompt = (f"Мне нужно составить теги из текста, не больше 10 слов, "
                  f"отправь в ответе только теги через запятую, без своих пояснений, ничего лишнего. Вот текст"
                  f": {request.text}")
        messages = [
            SystemMessage(content="Теги были сгенерированы по запросу."),
            HumanMessage(content=prompt)
        ]
        logging.warning('перед')
        # Отправка сообщений в GigaChat и получение ответа
        response = gigachat_chat(messages)
        tags = response.content
        logging.warning('ТЭГИ', tags)

        # Обновление базы данных с полученными тегами
        await update_database_with_tags(request.text_id, tags)

        return {"tags": tags}
    except Exception as e:
        # Обработка ошибок, если они возникнут
        raise HTTPException(status_code=500, detail=str(e))






