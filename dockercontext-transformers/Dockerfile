FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-devel

WORKDIR /workspace

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update 

RUN apt-get -y install \
    screen 

RUN ln -s /usr/bin/python3 /usr/bin/python

COPY requirements.txt /tmp

RUN pip install -r /tmp/requirements.txt

COPY transformers/ /workspace/