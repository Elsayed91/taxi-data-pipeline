## Airflow
Airflow serves as the orchestration tool for this project.

### Docker
The Dockerfile uses a lightweight image based on the slim airflow image, ensuring
efficient resource usage. It installs only the necessary packages. As gitsync is utilized,
there is no need to copy DAGs to the Docker image. Additionally, an init.sh script handles
the initialization and updating of the airflow database, along with the creation of
webserver users.

### Kubernetes
To pass values from applications to the pipeline, the pipeline_env configmap is utilized. The deployment for airflow includes both the scheduler and webserver. This setup is designed to offload workloads to Kubernetes pods/jobs, reducing pressure on the scheduler.

### Approach

For DAGs, the `KubernetesJobOperator` is employed, which offers increased flexibility compared to the default `KubernetesPodOperator`. This flexibility allows the use of Jinja/Helm templating inside the YAML files provided to the operator. This functionality seems like it should be available for the `KubernetesPodOperator`, but for some reason it isnt. I did leave notes for the Airflow team in a [discussion](https://github.com/apache/airflow/discussions/27650#discussioncomment-4612024). 

All tasks are executed using Kubernetes Pods, created using a pod template that is highly customizable and reusable across different scenarios. Additionally, a custom `SparkApplication` definition has been added to the library, enabling the execution of Spark jobs without the need for the `SparkKubernetesOperator`, resulting in reduced dependencies.


### Structure
```
├── dags
│   ├── addons
│   │   ├── parse_state.py
│   ├── batch_dag.py
│   ├── full_refresh_dag.py
│   ├── lambda_integration.py
│   ├── scripts
│   │   ├── aws_gcloud_data_transfer.sh
│   │   ├── dbt_run.sh
│   │   ├── train_model.sh
│   │   └── upload_dbt_results.py
│   └── templates
│       ├── pod_template.yaml
│       └── spark_pod_template.yaml
```
- `addons`: Contains a `parse_state.py` file that registers the `SparkApplication` kind and provides state parsing information.
- `batch_dag`: Executes a batch job whenever a new file is added to the S3 bucket. This DAG is triggered by a Lambda function, which provides the URI to download and process the new file.
- `full_refresh_dag`: Loads all previous data, avoiding 1-by-1 processing since Spark is used. While the batch DAG could be used for backfilling, Spark's capabilities make this approach less appealing.
- `lambda_integration`: A DAG used for integration testing of the Lambda function.
- `scripts`: Contains helper scripts for various components.  
    * `aws_gcloud_data_transfer`: facilitates data transfer from S3 to GCS using `gcloud transfer jobs`. 
    * `dbt_run`: simplifies the utilization of dbt, allowing for custom commands. 
    * `upload_dbt_results`: concatenates the files comprising the dbt docs into a single HTML file, which can then be hosted as a static website and uploaded to GCS.
- `templates` Includes standard pod and Spark pod templates. These templates are highly customizable and employ Jinja templating, offering maximum flexibility.

    template snippet:
    ```jinja
        {% if job.envFrom is defined  %}
        envFrom:
            {% for envFrom in job.envFrom %}
            - {% if envFrom.type == 'configMapRef' %}
                configMapRef:
                name: {{ envFrom.name }}
            {% else %}
                secretRef:
                name: {{ envFrom.name }}
            {% endif %}
            {% endfor %}
        {% endif %}
    ```
    which can be simply passed through the operator like so

    ```python
        t4 = KubernetesJobOperator(
            task_id="dbt",
            body_filepath=POD_TEMPALTE,
            command=["/bin/bash", f"{SCRIPTS_PATH}/dbt_run.sh"],
            arguments=[
                "--deps",
                "--seed",
                "--commands",
                "dbt run",
                "--generate-docs",
            ],
            jinja_job_args={
                "image": f"eu.gcr.io/{GOOGLE_CLOUD_PROJECT}/dbt",
                "name": "dbt",
                "gitsync": True,
                "volumes": [
                    {
                        "name": "gcsfs-creds",
                        "type": "secret",
                        "reference": "gcsfs-creds",
                        "mountPath": "/mnt/secrets",
                    }
                ],
                "envFrom": [{"type": "configMapRef", "name": "dbt-env"}],
            },
            envs={
                "DBT_PROFILES_DIR": f"{BASE}/dbt/app",
                "RUN_DATE": "{{ dag_run.conf.RUN_DATE }}",
            },
        )
    ```