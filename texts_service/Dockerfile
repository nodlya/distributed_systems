FROM python:3.11
WORKDIR /texts_service
COPY ./requirements.txt /texts_service/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /texts_service/requirements.txt
COPY ./app /texts_service/app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]