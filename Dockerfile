FROM python:rc-alpine

MAINTAINER Tyler Yox "tyox@objectsquared.com"

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python" ]

CMD[ "app.py" ]