FROM python:3.14

WORKDIR /root/app

COPY requirements.txt .
COPY scripts/install-dependencies.sh scripts/
RUN . scripts/install-dependencies.sh

COPY ./src .
