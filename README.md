


## **Testing**
### **Standard Unit Tests**
- Most functions have unit tests attached, the ones that do not are ones based completely off 3rd party libraries (like great expectations)
- There are some unit tests to test Airflow dag loading and default settings

### **Data Unit Tests**
there are **data** unit tests in DBT to test the model logic. this is done by providing a sample input and expected output and testing the model with them.

### **Integration Tests**
An integration test for the lambda function can be found in the tests/integration directory.

### **Data Quality**
- Data quality is validated on **ingestion** using Great Expectations.
- Data is divided into clean and triage data using Spark, where conditions are provided to ensure that clean data meets standard.
- All data source and models have dbt expectations data quality tests.


## **CI/CD**
**Github actions** is used for CICD workflows.
there are multiple workflows defined.

1. **Components**: this defines the workflow for docker images and kubernetes deployments.
If there is change in a docker directory, a new image is built and the corresponding deployment (if exists) is restarted.
If there is a change in a manifest directory, the change is applied.

2. **Code**: this includes automatically running tests and linting on code change.

3. **Terraform**: on changes to the terraform directory, terraform apply is run to apply these changes

4. **Lambda**: on changes to the lambda directory, integration test is carried out and then new lambda is deployed

Additionally **pre-commit** is used with a number of hooks to ensure that changes adhere to some best practices. 
<br>Note: to use the workflows, a GCP service account as well as the content of your `.env` file need to be added to your Github Secrets.


## Thoughts

- While it is usual to use multiple processing tools like Spark & DBT at the same time, for the scope of this project, just using Spark would provide maximum efficiency at lowest cost, however the decision to still use DBT is based on 2 reasons:
1. Documentation and Testing:
Data quality and unit testing for Spark can be done, but it is not as convinent as when using DBT.
Additionally the ability to document everything with extreme ease is absolutely valuable.
2. Showcase usage
Simply put, I wanted to display my ability at using different tools.

