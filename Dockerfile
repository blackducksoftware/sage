FROM python:3

ARG PIP_OPTIONS="--no-cache-dir"
ARG HTTP_PROXY
ARG HTTPS_PROXY

ENV HTTP_PROXY=$HTTP_PROXY
ENV HTTPS_PROXY=$HTTPS_PROXY

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install $PIP_OPTIONS -r requirements.txt

COPY . .

ENTRYPOINT ["/usr/local/bin/python3", "sage.py"]
