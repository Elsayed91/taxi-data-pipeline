ARG build_for=linux/amd64
FROM --platform=$build_for python:3.10.7-slim-bullseye
ENV PYTHONIOENCODING=utf-8 
#ENV DBT_HOME=/usr/app  DBT_PROFILES_DIR=/usr/app 
WORKDIR /
RUN apt-get -y update && apt-get install -y git && pip --no-cache-dir install dbt-bigquery==1.3.1 "elementary-data[bigquery]"


