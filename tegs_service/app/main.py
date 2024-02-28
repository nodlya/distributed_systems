import os
from fastapi import FastAPI, HTTPException
from langchain.schema import HumanMessage, SystemMessage
from langchain.chat_models.gigachat import GigaChat
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import asyncpg
import pika
import logging
import ast

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Укажите здесь домены, разрешенные для запросов, или "*", чтобы разрешить все домены
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Укажите методы, разрешенные для запросов
    allow_headers=["*"],  # Укажите здесь заголовки, разрешенные для запросов, или "*", чтобы разрешить все заголовки
)
# Авторизация в сервисе GigaChat
gigachat_credentials = "ZTkwNzU5MmQtYjk0NC00OWQ2LWFlZDItMzcyYzE5MDNkODYyOjdhNzY4NWM1LWZlMDEtNGMyMC04ZjVlLTE3MmU3NGFhNzY5Ng=="
gigachat_chat = GigaChat(credentials=gigachat_credentials, verify_ssl_certs=False)


class ChatRequest(BaseModel):
    text: str
    text_id: int


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

        # Отправка сообщений в GigaChat и получение ответа
        response = gigachat_chat(messages)
        tags = response.content

        # Обновление базы данных с полученными тегами
        # В этом месте нужно добавить код для обновления базы данных с тегами
        await update_database_with_tags(request.text_id, tags)

        return {"tags": tags}
    except Exception as e:
        # Обработка ошибок, если они возникнут
        raise HTTPException(status_code=500, detail=str(e))


db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
rabbit_host = os.environ.get("RABBIT_HOST")
redis_host = os.environ.get("REDIS_HOST")


async def update_database_with_tags(text_id, tags):
    conn = await asyncpg.connect(user=db_user, password=db_password, database=db_name, host=db_host)
    row = await conn.execute(f'UPDATE texts SET tegs = $1 WHERE id=$2', tags, text_id)
    await conn.close()


def callback(ch, method, properties, body):
    logging.warning('Message received, callback!')
    received_text = ast.literal_eval(body.decode('utf-8'))
    logging.warning(received_text)
    generate_tags(fanfic_text=received_text['fanfic_text'], id=received_text['id'])



connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host))
logging.warning(connection)
channel = connection.channel()
channel.queue_declare(queue='generate_tags')
channel.basic_consume(on_message_callback=callback, queue='generate_tags', auto_ack=True)
channel.start_consuming()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)
