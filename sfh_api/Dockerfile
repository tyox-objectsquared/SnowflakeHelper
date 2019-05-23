FROM python:alpine3.9

MAINTAINER Tyler Yox "tyox@objectsquared.com"

WORKDIR /app/sfh_api

COPY ./requirements.txt /app/sfh_api/requirements.txt

RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install -r /app/sfh_api/requirements.txt \
  && apk del build-dependencies

COPY . .

#run unit tests
RUN pytest /app/sfh_api/tests/unit/test_app.py

EXPOSE 5000/tcp

CMD ["python", "./src/main.py"]
