FROM python:3.6-alpine3.7
MAINTAINER Jianshen Liu <jliu120@ucsc.edu>

RUN apk --no-cache add bash

WORKDIR /root
COPY scripts scripts

ENTRYPOINT ["scripts/run"]
