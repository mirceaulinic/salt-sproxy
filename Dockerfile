FROM debian:stretch

MAINTAINER ping@mirceaulinic.net

ARG version="2017.7.8"

COPY ./ /var/cache/salt-sproxy/
RUN apt-get update \
 && apt-get install -y python-pip \
 && pip install salt==$version \
 && pip install /var/cache/salt-sproxy/ \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*
