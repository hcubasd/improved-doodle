FROM python:3.14

WORKDIR /root/app

COPY requirements.txt .
RUN python -m venv ~/.venv && . ~/.venv/bin/activate && python -m pip install -U pip -r requirements.txt

COPY ./src .
