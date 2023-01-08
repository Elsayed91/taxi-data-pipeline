FROM python:3.10.7-slim-bullseye

WORKDIR /app
COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN rm -rf requirements.txt && \
    rm -rf /var/cache/apt/* && \
    rm -rf /root/.cache/pip

ENTRYPOINT ["python]