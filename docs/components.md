


## <u>Spark</u>
### Dockerfile
the dockerfile builds on the official spark image, but adds the needed PIP packages and jars to it.
The jars in use are gcs connector, bigquery connector and JMX prometheus java agent for monitoring and metrics tracking.

### Kubernetes
Since I am running a kubernetes cluster on GKE anyway, spark on k8s felt like a better choice than a managed dataproc cluster. 
Spark on k8s offers a lot of flexibility and is very powerful.

### Spark logic
the `scripts dir` has 4 files:
- `batch` defines the spark batch job, which is run everytime a new file is added to the S3 bucket.
- `initial_load` defines the spark job that runs desired operations on all previous data up to date. It also serves as a full refresh option.
- `configs` holds some configurations and variables like queries, just to reduce the noise in the main logic files.
- `spark_fns` holds helper functions.
the helper functions are divided into 2 use cases, 1st is to overcome the inconsistency in schemas and the 2nd is just a way to pack the spark logic into a function.

<br>the code also makes use of 2 notable spark options:
1. `datePartition` which ensures that the pipeline is idempotent
2. `bigQueryJobLabel` which provides the jobs with a label that can be used to query `INFORMATION_SCHEMA` later on to get information related to the jobs like billed bytes and such.

#### Inconsistent Schema
the files have a lot of fields that are supposed to be of `float` datatype, however as they are not populated (null) the system infers an integer datatype. this is a very random pattern and using differenet spark otpions like merge schema, overwrite schema, setting a schema, casting, etc, does not resolve the error. Attempting to load with different tools like bigquery or dbt does not resolve the issue either. 

To identify the files with incorrect schema seems to be the only solution. Howeer runing a spark job on a file by file basis is extremely inefficient. so to ensure that we are still making good use of the distributed processing I created some functions that basically read the metadata from the file in GCS (not the whole file) and save the schema in a dataframe, then it would group the tables by similar schema, and return a list containing lists of items that have the same schema, which is then passed to spark.


## <u>Great Expectations</u>

The `dv_helpers.py` module defines a class `ConfigLoader` which loads and parses a YAML
configuration file and substitutes the values of environmental variables in the YAML
files.

The code also defines a helper function `retrieve_nested_value` to retrieve the value
associated with a given key in a nested mapping.

The `data_validation.py` module uses the Great Expectations library to perform data
validation. It uses the `ConfigLoader` class to load and parse the Great Expectations and
checkpoint YAML files. The code sets up a Spark context, runs the checkpoints, retrieves
the results, and validates the success percentage against a threshold. The code also
builds the data documentation folder in the data_docs_sites.

Notes:

- The validation is done using SparkDF. Running the validation on a 2 million row file
takes 20m locally, less than 4 minutes using distributed spark.
- A threshold is defined, although the threshold is set at a very low value, it canb be
set at an appropriate value to fail the airflow DAG if the data quality does not pass
standards.
- docs are uploaded to GCS and loaded via docs-app component, which is a flask app that
  runs static websites. 


## <u>AWS Lambda</u>

The lambda function triggers an airflow DAG in a GKE cluster when an object is added to an
S3 bucket. The function retrieves the bucket name and object key from the event data,
constructs an object URI in the format "s3://bucket_name/key". It then retrieves cluster
information, DAG name, and namespace from environment variables.

The module authenticates with Google Cloud Platform (GCP) using a service account key and
uses the Google Kubernetes Engine (GKE) API to retrieve information about a specific
cluster and create a Kubernetes client configuration and API client. It retrieves a list
of pods in the specified namespace and searches for a pod with a name containing
"airflow." If found, the Kubernetes API is used to execute the command string on the pod
to trigger the DAG.

It can be extended to allow cluster resizing in case the cluster is downscaled to 0.

### **Integration Test**
The lambda comes with an integration test that can be found in tests/integration/lambda.
the test packages the lambda function and uses localstack and terraform to create pseudo
AWS infrastructure. the lambda function is run on it, with the result being a DAG trigger.
the dag `lambda_integraton_test` receives input and validates it. To run the integration
test simply use `make run_lambda_integration_test`


## <u>DBT</u>

DBT is used for 2 main purposes. 1st to create a ready-to-use for ML training purposes
table, i.e the model wouldn't have to preproces the data.

Assuming a team of data scientists use the data often for experiments, pre-processing
~12-16 million rows can get expensive quickly. This approach cuts down the compute
expenses related to pre-processing. It can be made even cheaper by using views or external
tables, which would reduce the storage costs, but will not be as quick as native tables.

the 2nd purpose is to keep clear documentation of the content of the tables and enable
easy testing for data quality and unit testing.

While a lot of models can be created with the existing data, I've created 2 models, an ML model and a BI reporting model.

### Notable Packages in use
- `elementary` is used to provide extra information regarding tests and processing
  statistics. 
- `dbt_expectations` is used to validate data quality.
- `dbt_datamocktool` is used to run unit tests on sample data.

### Static Docs
dbt docs and elementary docs are both automatically uploaded to a docs-specific GCS
bucket. dbt docs undergo a small transformation to turn the different files into a single
file to make it easier to handle as a static file.

both of them (along with great expectation docs) are hosted through the docs_app
component.

the docs are generated through a script which is passed through airflow. for more
information see the airflow scripts section.

### Table Materialization
1. ML Model: Incremental Strategy. This table needs to be fast to query the whole dataset, additionally the whole purpose of the table is to allow the datascientists to skip the continuous pre-processing, that means the table will be queried often, so an incremental strategy is best here.

2. BI Model: View. While A view is best for getting you from point A to point B, the data from this view will be used by a Grafana dashboard that will be refreshed once per month, since the data itself won't be queried and it is fairly static, a view will suffice and it will spare the costs of using BigQuery storage. Additionally the data is fairly small in size (> 2gb).

## <u>Machine Learning</u>
### ML train
- `train.py` trains a model and tunes the hyperparameters, this is done for the initial load only.
- `retrain.py` uses continuous training to extend the existing model.
- `serve.py` serves the model as a flask app.
For training a machine with higher ram is used. GPUs are not available for usage during GCP trial, and also because the training script only uses up about 9-10.5 gb of RAM, a 16GB machine is used for this scenario. Kindly note that this is enot optimal and when doing hyperparameter tuning it takes hours if the full dataset is loaded. 

### MLFlow
MLFlow is used to log metrics and models to the MLFlow registry which is linked to GCS. 




## <u>Other components</u>
### Postgres
A standard Postgres service that serves multiple components (Airflow & Mlflow).
It comes with a small tweak to allow creation of multiple databases on initialization.
this is done through a script `create-multiple-postgresql-databases.sh` which looks up the environmental variable for any environmental variables with an _DB suffix. for example `AIRFLOW_DB` would mean that it needs to create a database for airflow. then it looks up `AIRFLOW_DB_USER` and `AIRFLOW_DB_PASSWORD`. It also has the ability to omit these and fall back to a default value, which basically the component name, in this exmaple it would be `AIRFLOW`.

### Prometheus
A prometheus server that collects various metrics.

the metrics collected are:
- Airflow (statsd)
- Spark (spark-operator+JMX prometheus java agent)
- Kubernetes State (kube-state-metrics) 
- Postgres (prometheus-postgres-exporter)

### Grafana
### metric exporters
this includes statsd, prometheus-postgres-exporter and kube-state-metrics.
After considering the tradeoffs, I found that combining these 3 into a singular deployment is suitable for this use case. itt helps simplify the management of the deployment, reduces resource consumption and reduces latency between the services.

### k8s common
this directory includes components that are not specific to a specific component. this includes pvc, crds, pipeline environmental variables configmap, rbac and a load balancer.

the load balancer is used to expose multiple services that are intended to be accessed by users. 
the decision to use one load balancer for all of them is simply to reduce costs, as each external IP created via load balancers incurs significant costs.
combining them all reduces this cost significantly while providing access to different application interfaces. 

## <u>Static Docs App</u>
A very simple flask app that allows serving of multiple static files that are located in GCS.
In this iteration it hosts Great Expectations, DBT and Elementary docs. 