FROM mhart/alpine-node:11

MAINTAINER Tyler Yox "tyox@objectsquared.com"

RUN yarn global add serve

WORKDIR /app

COPY ./build .

EXPOSE 80/tcp

CMD ["serve", "-p", "80", "-s", "."]

