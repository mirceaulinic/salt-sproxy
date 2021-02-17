FROM python:3.7.10-slim-stretch

MAINTAINER ping@mirceaulinic.net

ARG SALT_VERSION="2019.2.5"

COPY ./ /var/cache/salt-sproxy/
COPY ./master /etc/salt/master

RUN apt-get update \
 && apt-get install -y python-zmq gcc \
 && pip --no-cache-dir install salt==$SALT_VERSION \
 && pip --no-cache-dir install /var/cache/salt-sproxy/ \
 && rm -rf /var/cache/salt-sproxy/ \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*
