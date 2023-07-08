# Table of Content

<ol>
<li><a href="#airflow">Airflow</a></li>
<li><a href="#spark">Spark</a></li>
<li><a href="#great-expectations">Great Expectations</a></li>
<li><a href="#aws-lambda">AWS Lambda</a></li>
<li><a href="#dbt">DBT</a></li>
<li><a href="#machine-learning">Machine Learning</a></li>
<li><a href="#other-components">Other Components</a></li>
<ul>
    <li><a href="#postgres">Postgres</a></li>
    <li><a href="#prometheus">Prometheus</a></li>
    <li><a href="#grafana">Grafana</a></li>
    <li><a href="#static-docs-app">Static Docs App</a></li>
    <li><a href="#kubernetes-common-directory">Kubernetes Common Directory</a></li>
</ul>
</ol>


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

## <u>Spark</u>

### Dockerfile

The Dockerfile builds on the official Spark image while incorporating the necessary PIP packages and JAR files. The JAR files utilized include the GCS connector, BigQuery connector, and JMX Prometheus Java Agent for monitoring and metrics tracking.

### Kubernetes

Given that a Kubernetes cluster is already in use on GKE, deploying Spark on Kubernetes (Spark on k8s) was deemed more favorable than opting for a managed Dataproc cluster.

### Spark Logic

The `scripts` directory consists of four files:

-   `batch`: Defines the Spark batch job, which is executed whenever a new file is added to the S3 bucket.
-   `initial_load`: Defines the Spark job responsible for performing desired operations on all previous data up to the present, effectively serving as a full refresh option.
-   `configs`: Contains configurations and variables, such as queries, aimed at reducing noise in the main logic files.
-   `spark_fns`: Contains helper functions that address specific use cases within the Spark logic.

The helper functions are categorized into two main use cases. The first use case tackles the challenge of inconsistent schemas, while the second use case provides a structured approach to encapsulating Spark logic within a function.

Moreover, the code leverages two notable Spark options:

1.  `datePartition`: Ensures that the pipeline remains idempotent by partitioning data based on date.
2.  `bigQueryJobLabel`: Assigns a label to the jobs, facilitating future querying of the `INFORMATION_SCHEMA` to retrieve information such as billed bytes.

#### Inconsistent Schema

One major challenge in this project was the lack of uniformity in the schema across the NY Taxi Data, especially for older records. Some columns that were expected to have `float` data types were empty and had an `int` data type instead.

With a large number of files (~160), manually checking the schema for each file was impractical. Although using a loop in Spark to read the data one by one was technically feasible, it undermined the purpose of using Spark in the first place. I explored various solutions, including Spark's `MergeSchema`, `OverwriteSchema`, Type Casting in `sparksql`, but none of them yielded the desired results.

After extensive research, I discovered an alternative approach using pyarrow. By leveraging pyarrow, I could extract the metadata of the Parquet files, which included the schema information. This significantly reduced the processing overhead. I stored the schema data and file names in a dataframe and grouped files with similar schema columns. Ultimately, I obtained a list of lists, where each sublist represented files with similar schemas. These lists were then processed using Spark to enforce a unified schema before loading the data into BigQuery.




 ## <u>Great Expectations</u>

The `dv_helpers.py` module introduces the `ConfigLoader` class, responsible for loading and parsing a YAML configuration file while handling the substitution of environmental variable values in the YAML files. It also includes the `retrieve_nested_value` helper function for retrieving values associated with specific keys within nested mappings.

In the `data_validation.py` module, the Great Expectations library is employed for data validation purposes. It utilizes the `ConfigLoader` class to load and parse the Great Expectations and checkpoint YAML files. The code establishes a Spark context, executes the checkpoints, retrieves the results, and validates the success percentage against a predefined threshold. Additionally, the code generates the data documentation folder within the `data_docs_sites` directory.

Key Points:

-   Data validation is performed using SparkDF, with local execution taking approximately 20 minutes for a 2 million row file. Distributed Spark reduces the execution time to less than 4 minutes.
-   A threshold is defined to determine the success percentage for data quality. It can be adjusted to fail the Airflow DAG if data quality standards are not met.
-   Documentation is uploaded to Google Cloud Storage (GCS) and served through the Flask app component.

## <u>AWS Lambda</u>

The lambda function triggers an Airflow DAG in a GKE cluster when an object is added to an S3 bucket. It extracts the bucket name and object key from the event data and constructs an object URI in the format "s3://bucket\_name/key". The module authenticates with Google Cloud Platform (GCP) using a service account key and utilizes the Google Kubernetes Engine (GKE) API to retrieve cluster information, DAG name, and namespace from environment variables.

The module further interacts with the GKE API to create a Kubernetes client configuration and API client, enabling it to retrieve a list of pods in the specified namespace and search for a pod with a name containing "airflow." If found, the Kubernetes API is used to trigger the DAG by executing the command string on the pod.

Note: The functionality can be extended to allow cluster resizing.

### **Integration Test**

The lambda includes an integration test located in `tests/integration/lambda`. The test packages the lambda function and employs localstack and Terraform to create pseudo AWS infrastructure. The lambda function is executed within this environment, resulting in a triggered DAG. The `lambda_integration_test` DAG handles the input and performs validation. To run the integration test, use the command `make run_lambda_integration_test`.

## <u>DBT</u>

DBT serves two main purposes in the project. Firstly, it facilitates the creation of a ready-to-use table for ML training purposes, reducing the need for preprocessing by ML models. This approach helps minimize compute expenses associated with preprocessing large datasets. Additionally, DBT assists in maintaining clear documentation of table content and enables easy data quality testing and unit testing.

Key Packages in Use:

-   `elementary` provides additional information regarding tests and processing statistics.
-   `dbt_expectations` validates data quality.
-   `dbt_datamocktool` runs unit tests on sample data.

Static documentation for DBT and Elementary is uploaded to a dedicated GCS bucket. The DBT documentation is transformed into a single file for easier handling as a static resource. Both the DBT and Great Expectations documentation are hosted through the Flask app component.


## <u>Machine Learning</u>

### ML Train

-   `train.py` trains a model and tunes hyperparameters.
-   `serve.py` serves the model as a Flask app.

Training is performed using a machine with higher RAM. While GPU usage is unavailable during the GCP trial period, a 16GB machine is sufficient for the training script, which typically utilizes around 9-10.5GB of RAM. It is important to note that this setup is not optimal, and hyperparameter tuning can be time-consuming when using the full dataset.

`MLFlow` is utilized to log metrics and models in the MLFlow registry, which is linked to GCS.

## <u>Other Components</u>

### Postgres

A standard Postgres service is employed to serve multiple components such as Airflow and MLFlow. A script, `create-multiple-postgresql-databases.sh`, allows the creation of multiple databases on initialization. The script retrieves environmental variables with the `_DB` suffix (e.g., `AIRFLOW_DB`), which indicate the need to create a database for the specific component. It can also fallback to default values if specific variables are not provided.

### Prometheus

The Prometheus server collects various metrics from different sources:

-   Airflow (Statsd)
-   Spark (Spark Operator + JMX Prometheus Java Agent)
-   Kubernetes State (kube-state-metrics)
-   Postgres (prometheus-postgres-exporter)

### Grafana

This section includes metric exporters, namely Statsd, Prometheus Postgres Exporter, and kube-state-metrics. These three exporters are combined into a single deployment to simplify management, reduce resource consumption, and minimize latency between services.

### <u>Static Docs App</u>

The Static Docs App is a simple Flask app that serves multiple static files located in GCS. In this project, it hosts the documentation for Great Expectations, DBT, and Elementary.

### Kubernetes Common Directory

This directory contains components that are not specific to a particular component. It includes PersistentVolumeClaims (PVC), Custom Resource Definitions (CRDs), pipeline environmental variables configmap, RBAC, etc.