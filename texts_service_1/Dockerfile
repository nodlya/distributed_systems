FROM python:3.11
WORKDIR /texts_service_1
COPY ./requirements.txt /texts_service_1/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /texts_service_1/requirements.txt
COPY ./app /texts_service_1/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]