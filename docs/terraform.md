## Table Of Contents

- [**Structure**](#--structure--)
- [**What is being provisioned**](#--what-is-being-provisioned--)
  * [**IAM**](#--iam--)
  * [**BIGQUERY**](#--bigquery--)
  * [**GCS**](#--gcs--)
  * [**GKE**](#--gke--)
  * [**S3**](#--s3--)
  * [**LAMBDA**](#--lambda--)
  * [**SECRETSMANAGER**](#--secretsmanager--)
- [**Approach**](#--approach--)
  * [**How it works**](#--how-it-works--)
  * [**Nested Values**](#--nested-values--)

## **Structure**
```
├── configuration
│   ├── aws.yaml
│   └── gcp.yaml
├── main.tf
├── modules
│   ├── bigquery.tf
│   ├── files
│   │   ├── bq_schemas
│   │   │   ├── historical_yellow.json
│   │   │   └── stg_yellow.json
│   │   └── package_lambda.sh
│   ├── gcs_buckets.tf
│   ├── gke.tf
│   ├── iam.tf
│   ├── lambda.tf
│   ├── s3_buckets.tf
│   ├── secretsmanager.tf
│   └── variables.tf
├── providers.tf
└── versions.tf
```

* configuration directory holds yaml files that has the configurations for each cloud
  provider.
* modules directory holds the different components that will be created. It might be
  favorable to declare modules in separate directories, however as re-usability is not an
  issue, I've opted for a simple setup for this project. 
* files directory holds schemas needed for bigquery tables and a script that prepares code
needed to deploy the lambda function.

## **What is being provisioned**

Each `.tf` file includes general documentation for what resources will be created.
Below is specific-documentation for the resources that will be created within the scope of
the project.

### **IAM**
2 service accounts with necessary permissions, and custom roles. One for the lambda
function to be able to communicate with GCP, and the other is for GKE workload identity &
Spark job. Note: owner permission is given here to the GKE workload identity service
account, this is NOT a best practice, but I've opted for it as the scope of the project
allows it.

### **BIGQUERY** 
datasets are provisioned and some tables as well, the tables are created with time
partitioning, clustering fields and schemas.

### **GCS**
5 buckets are created for things like raw data, doc sites (great expectations, dbt,
elementary), spark processing bucket, etc. The code also includes a way to sync content of
project folder with a folder in a GCS bucket. this is mainly used to upload the
expectations needed by Great Expectations.

### **GKE**
a zonal cluster with workload identity configured is created, along with 3 node pools.
The node pools serve different purposes.
- Base: for low pressure deployment and jobs, and mainly always running deployments.
this uses an e2-small, and with autoscaling it scales down to 1 node msot of the time.
Being a zonal cluster, you don't pay for management fees, only for the compute.
with this setup it doesn't even amount to 10EUR a month running the whole month long.
- Spark Jobs: as the name says, for spark jobs, this includes a machine type with higher
memory to accomodate the spark jobs.
- ML: High memory machine for machine learning purposes. this option is used as GPU is not 
available for use during gcp trial.

All 3 node pools have auto scaling on. the spark and ML node pools will always scale down
to 0 if no jobs are running.

### **S3**
creates a bucket with public read ACL. this bucket serves as a substitute bucket for the
actual bucket that receives the NYTAXI data.

### **LAMBDA**
creates 1 lambda function that is triggered when a file is added to the S3 bucket.
NOTE: the lambda code is not as parametrized as the GCP code. this is mainly because the
scope of AWS in this project is really narrow and limited to only this particular
function.

### **SECRETSMANAGER**
creates a secret to use GCP service account key in the lambda function safely.


## **Approach**
In order to enhance code organization, readability and resuability, I've opted to use an
approach wherein the configuration is declared in yaml files.

### **How it works**
to illustrate, let's say we want to to create a usable config file like this aws.yaml
```yaml
S3:
  - name: ${AWS_DUMMY_BUCKET}
    acl: "public-read"
LAMBDA:
  - name: "die-lambda"
    dependencies_path: "files/lambda/dependencies.zip"
    vars:
      PROJECT: "${PROJECT}"
      GCP_ZONE: "${GCP_ZONE}"
      GKE_CLUSTER_NAME: "${GKE_CLUSTER_NAME}"
      DAG_NAME: "lambda_integration_test"
      TARGET_NAMESPACE: "default"
    trigger_bucket: "${AWS_DUMMY_BUCKET}"
    code_path: "./../../components/lambdafn"
    memory_size: 128
SECRETSMANAGER:
  - name: "gcp_key"
    type: "file"
    secret_string: "files/lambda_key.json"
```

we first define the resources, let's take the S3 as an example.
```tf
resource "aws_s3_bucket" "bucket" {
  for_each = { for idx, bucket in var.s3-buckets : idx => bucket if var.s3-buckets != null }
  bucket   = each.value.name

}

resource "aws_s3_bucket_acl" "bucketacl" {
  for_each = { for idx, bucket in var.s3-buckets : idx => bucket if var.s3-buckets != null }
  bucket   = aws_s3_bucket.bucket[each.key].id
  acl      = each.value.acl
}
```

The Terraform resources must be defined with for loops to work with the lists in the yaml
config file.

After that, you need to declare a variable that holds the general structure for this
input. At this part, you also define optional and default values. Here's an example for
the S3 buckets:

```tf
variable "s3-buckets" {
  type = list(object(
    {
      name = string
      acl  = optional(string, "public-read")
    }
  ))
  default = null
}
```

here acl is optional with "public-read" as a default value, this means that if acl was NOT
provided in the yaml file, it will not raise an error and public-read value you will be
used.


At this point, a configuration file that has the desired values can be created, and then
parsed ike so.

```tf
locals {
  envs          = { for tuple in regexall("(.*?)=\"(.*)\"", file("${path.module}/../.env")) : tuple[0] => tuple[1] }
  aws           = yamldecode(templatefile("${path.module}/configuration/aws.yaml", local.envs))

}

module "project" {

  source           = "./modules/"
  project          = local.envs["PROJECT"]
  region           = local.envs["GCP_REGION"]
  location         = local.envs["GCP_ZONE"]
  s3-secrets       = local.aws["SECRETSMANAGER"]
  s3-buckets       = local.aws["S3"]
  lambda           = local.aws["LAMBDA"]
}

```

the `yamldecode` will read the yaml file. the `templatefile` will replace any ${VAR} with
the values from local.envs.

this means that you can use a pre-existing `.env` file as the source for your enviornmental
variables and forego `.tfvars`. 

Adding new resources is as simple as adding a new item to the yaml list. For example, to
add a new S3 bucket named "zelda", the Yaml file would look like this:
```tf
S3:
  - name: ${AWS_DUMMY_BUCKET}
    acl: "public-read"
  - name: zelda
```

since acl was not provided, it will be "public-read" by default. 


### **Nested Values**

In the yaml config, you could declare each resource separately, this would make the
implementation much easier, but will mean repetition of some values, for example, consider
you are creating a config file for bigquery datasets. You could create an object for the
datasets and an object for tables, or you could create an object for the datasets and
include the tables in each dataset within it. 

The 2nd approach has a forte and a con, the forte being not having to reference the
dataset for each table like you would if tables are their separate objects. the con is
that you need to code a bit to retrieve the data relevant to the nested table.

this can be done using terraform functions, for example:

```tf
locals {
  bigquery = flatten([for idx, value in var.bigquery :
    [for table in try(value.tables, null) : {
      "dataset_id"         = try(value.dataset_id, null)
      "table_id"           = try(table.table_id, null)
      "time_partitioning"  = try(table.time_partitioning, null)
      "partitioning_type"  = try(table.time_partitioning.type, null)
      "partitioning_field" = try(table.time_partitioning.field, null)
      "expiration_ms"      = try(table.time_partitioning.expiration_ms, null)
      "clustering_fields"  = try(table.clustering_fields, null)
      "schema"             = try(table.schema, null)
      "view"               = try(table.view, null)
    }]
    if try(value.tables, null) != null
  ])
}
```

this will create a list that includes each table, and naturally the dataset_id. 

Note: this approach makes heavy use of `dynamic` keyword, which allows you to dynamically
set attribtues based on conditions.



