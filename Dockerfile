FROM nikolaik/python-nodejs:python3.7-nodejs10

MAINTAINER Tyler Yox "tyox@objectsquared.com"

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

RUN npm install -g pm2

COPY . /app

EXPOSE 3000

WORKDIR /app/webapp

# commands to start NodeJS server in background and Flask server in foreground
ENTRYPOINT pm2 start npm -- start && python ../snowflake_alerts/app.py
