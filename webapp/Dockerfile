FROM node:8 as react-build

MAINTAINER Tyler Yox "tyox@objectsquared.com"

WORKDIR /app

COPY . ./

RUN yarn

RUN yarn build

FROM mhart/alpine-node:11

RUN yarn global add serve

COPY --from=react-build /app/build .

EXPOSE 80/tcp

CMD ["serve", "-p", "80", "-s", "."]

