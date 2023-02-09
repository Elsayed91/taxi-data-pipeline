FROM python:3.8-slim-buster
WORKDIR /home

RUN pip install --upgrade pip && \
    pip install --no-cache-dir kafka-python pyarrow

RUN rm -rf /var/cache/apt/* && \
    rm -rf /root/.cache/pip

