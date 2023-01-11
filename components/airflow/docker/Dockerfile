FROM apache/airflow:slim-2.5.0-python3.10
# COPY --chmod=0755 init.sh /opt/airflow/init.sh
COPY init.sh /opt/airflow/init.sh
USER 0
RUN chmod 0755 /opt/airflow/init.sh
USER 50000
RUN pip3 install --user airflow-kubernetes-job-operator==2.0.12 \
    psycopg2-binary==2.9.5 statsd==4.0.1







    #apache-airflow-providers-cncf-kubernetes    
  
  
  
  
  
  
  
  
  
  
  
