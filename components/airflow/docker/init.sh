#!/bin/bash
# this scripts initializes and upgrades an arflow DB and also creates an admin and a viewer user at initiation.
airflow db init
airflow db upgrade
airflow users create -r Admin -u ${AIRFLOW_ADMIN_USER} -e admin@example.com -f admin -l user -p ${AIRFLOW_ADMIN_PASSWORD}
airflow users create -r Viewer -u ${AIRFLOW_VIEWER_USER} -e viewer@example.com -f viewer -l viewer -p ${AIRFLOW_VIEWER_PASSWORD}
