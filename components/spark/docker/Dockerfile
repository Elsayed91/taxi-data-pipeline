# FROM apache/spark-py:v3.1.3
FROM apache/spark-py:v3.3.1

WORKDIR /
#Reset to root to run installation tasks
USER 0   
RUN apt-get update -y -q && apt-get upgrade -y -q && apt-get install wget -y -q
RUN rm $SPARK_HOME/jars/guava-*jar
ADD https://repo1.maven.org/maven2/com/google/guava/guava/31.1-jre/guava-31.1-jre.jar $SPARK_HOME/jars
RUN chmod 644 $SPARK_HOME/jars/guava-31.1-jre.jar
RUN wget https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-hadoop3-latest.jar -O /opt/spark/jars/gcs-connector-hadoop3-latest.jar
RUN chmod 644 $SPARK_HOME/jars/gcs-connector-hadoop3-latest.jar
RUN wget https://github.com/GoogleCloudDataproc/spark-bigquery-connector/releases/download/0.27.1/spark-3.1-bigquery-0.27.1-preview.jar -O /opt/spark/jars/spark-3.1-bigquery-0.27.1-preview.jar
RUN chmod 644 $SPARK_HOME/jars/spark-3.1-bigquery-0.27.1-preview.jar
ADD https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.11.0/jmx_prometheus_javaagent-0.11.0.jar /prometheus/
RUN chmod 644 /prometheus/jmx_prometheus_javaagent-0.11.0.jar
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && rm -rf requirements.txt && rm -rf /var/cache/apt/*
RUN mkdir -p /etc/metrics/conf
COPY --chmod=0755 [ "conf/metrics.properties", "conf/prometheus.yaml", "/etc/metrics/conf/"]

# Specify the User that the actual main process will run as
USER 185
ENTRYPOINT [ "/opt/entrypoint.sh" ]

