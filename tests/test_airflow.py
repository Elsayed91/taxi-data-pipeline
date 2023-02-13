from airflow.models import DagBag
import glob
import importlib.util
import os

import pytest

from airflow.models import DAG
from airflow.utils.dag_cycle_tester import check_cycle

os.environ["ML_SERVING_MANIFEST"] = "components/ml_serve/manifests/serving.yaml"


def test_no_import_errors():
    dag_bag = DagBag(dag_folder="components/airflow/dags", include_examples=False)
    assert len(dag_bag.import_errors) == 0, "No Import Failures"


def test_retries_present():
    dag_bag = DagBag(dag_folder="components/airflow/dags", include_examples=False)
    for dag in dag_bag.dags:
        retries = dag_bag.dags[dag].default_args.get("retries", [])
        error_msg = f"Retries not set to 0 for DAG {dag}"
        assert retries == 0, error_msg


def test_in_cluster():
    dag_bag = DagBag(dag_folder="components/airflow/dags", include_examples=False)
    for dag in dag_bag.dags:
        in_cluster = dag_bag.dags[dag].default_args.get("in_cluster", [])
        error_msg = f"in_cluster not set for DAG {dag}"
        assert in_cluster == True, error_msg


DAG_PATH = os.path.join(os.path.dirname(__file__), "..", "components/airflow/dags/*.py")
DAG_FILES = glob.glob(DAG_PATH, recursive=True)


@pytest.mark.parametrize("dag_file", DAG_FILES)
def test_dag_integrity(dag_file):
    # https://github.com/josephmachado/beginner_de_project/blob/master/tests/dags/test_dag_integrity.py
    module_name, _ = os.path.splitext(dag_file)
    module_path = os.path.join(DAG_PATH, dag_file)
    mod_spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(mod_spec)
    mod_spec.loader.exec_module(module)

    dag_objects = [var for var in vars(module).values() if isinstance(var, DAG)]
    assert dag_objects

    for dag in dag_objects:
        check_cycle(dag)
