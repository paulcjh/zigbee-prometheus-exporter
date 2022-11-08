FROM python:3.11.0-slim

WORKDIR /core

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

#CMD [ "python","-m","watchgod","--extensions=.json","app.start" ]
CMD ["python", "./app/__init__.py"]
