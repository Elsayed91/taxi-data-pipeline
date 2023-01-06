"""
Data Validation module with Great Expectations.
It loads great_expectations and checkpoint yaml files via ConfigLoader helper class,
which does env substitutions to add information like "file uri" to the config file.

After setting up context, the scripts runs the checkpoints and retrives the results.
The result is a huge dict with all run statistics, it extract "success_percent" from it.
then it validates the success percentage against a threshold defined in the 
VALIDATION_THRESHOLD constant. If the success percentage is below the threshold, a
ValidationError is raised.
It also builds the data docs folder in the data_docs_sites
"""

from pyspark.sql import SparkSession
from great_expectations.data_context.types.base import DataContextConfig
from great_expectations.data_context import BaseDataContext
from dv_helpers import *

# Constants for configuration file paths
CONFIG_DIR = os.getenv("GE_CONFIG_DIR")
GE_CONFIG_PATH = f"{CONFIG_DIR}/great_expectations.yaml"
CP_CONFIG_PATH = f"{CONFIG_DIR}/checkpoint.yaml"

# Constants for validation threshold and validation error message
THRESHOLD_PERCENTAGE = os.getenv("VALIDATION_THRESHOLD")
VALIDATION_THRESHOLD = float(THRESHOLD_PERCENTAGE.replace("%", "")) / 100  # type: ignore
VALIDATION_ERROR_MSG = "Validation failed: success percentage below threshold"


def main():
    # Load Great Expectations config and checkpoint config
    ge_config = ConfigLoader(GE_CONFIG_PATH).load_config()
    cp_config = ConfigLoader(CP_CONFIG_PATH).load_config()

    # Create a DataContext and add the checkpoint
    data_context = BaseDataContext(DataContextConfig(**ge_config))
    data_context.add_checkpoint(**cp_config)

    # Run the checkpoint and retrieve the result
    cp_result = dict(data_context.run_checkpoint(checkpoint_name="cp"))
    print(cp_result)
    # Build the data docs
    data_context.build_data_docs()

    # Retrieve the success percentage from the checkpoint result
    success_percentage = list(retrieve_nested_value(cp_result, "success_percent"))[0]

    # Validate the success percentage against the threshold
    if success_percentage < VALIDATION_THRESHOLD:
        raise ValidationError(VALIDATION_ERROR_MSG)
    else:
        print(f"Validation successful with a {success_percentage}% success percentage.")


if __name__ == "__main__":
    spark = SparkSession.builder.getOrCreate()
    main()
