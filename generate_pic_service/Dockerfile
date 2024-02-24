FROM python:3.11
WORKDIR /generate_pic_service
COPY ./requirements.txt /generate_pic_service/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /generate_pic_service/requirements.txt
COPY ./app /generate_pic_service/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]