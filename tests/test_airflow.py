from airflow.models import DagBag


def test_no_import_errors():
    dag_bag = DagBag()
    assert len(dag_bag.import_errors) == 0, "No Import Failures"


def test_retries_present():
    dag_bag = DagBag()
    for dag in dag_bag.dags:
        retries = dag_bag.dags[dag].default_args.get("retries", [])
        error_msg = f"Retries not set to 0 for DAG {dag}"
        assert retries == 0, error_msg


def test_in_cluster():
    dag_bag = DagBag()
    for dag in dag_bag.dags:
        in_cluster = dag_bag.dags[dag].default_args.get("in_cluster", [])
        error_msg = f"in_cluster not set for DAG {dag}"
        assert in_cluster == True, error_msg
