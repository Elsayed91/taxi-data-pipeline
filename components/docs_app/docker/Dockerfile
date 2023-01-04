FROM python:3.10-slim-buster

RUN apt-get update && apt-get -y install netcat && apt-get clean

WORKDIR /app

COPY --chmod=0755 . .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && rm -rf requirements.txt && rm -r /root/.cache && rm -rf /var/cache/apt/*

CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]

