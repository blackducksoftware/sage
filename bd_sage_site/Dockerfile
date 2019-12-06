# Derived from https://docs.docker.com/compose/django/

# Use python 3.8 on Debian, slimmed-down version
FROM python:3.8.0-slim-buster

# Force log messages to be flushed immediately rather than buffered
ENV PYTHONBUFFERED=1

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/