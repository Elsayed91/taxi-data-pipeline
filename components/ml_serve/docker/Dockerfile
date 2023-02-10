# https://github.com/pycaret/pycaret-streamlit-google/blob/master/Dockerfile
FROM python:3.10.7-slim-bullseye

RUN pip install virtualenv
ENV VIRTUAL_ENV=/venv
RUN virtualenv venv -p python3
ENV PATH="VIRTUAL_ENV/bin:$PATH"

WORKDIR /app
# copying all files over
COPY . /app

# Install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN rm -rf requirements.txt && \
    rm -rf /var/cache/apt/* && \
    rm -rf /root/.cache/pip


ENV PORT 8501
CMD streamlit run serve.py

# streamlit-specific commands for config
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
RUN mkdir -p /root/.streamlit
RUN bash -c 'echo -e "\
[general]\n\
email = \"\"\n\
" > /root/.streamlit/credentials.toml'

RUN bash -c 'echo -e "\
[server]\n\
enableCORS = false\n\
" > /root/.streamlit/config.toml'