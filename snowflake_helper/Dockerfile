FROM python:alpine3.9

MAINTAINER Tyler Yox "tyox@objectsquared.com"

WORKDIR /app

COPY ./requirements.txt requirements.txt

RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install -r requirements.txt \
  && apk del build-dependencies

COPY . .

EXPOSE 5000/tcp

CMD ["python", "/app/app.py"]
