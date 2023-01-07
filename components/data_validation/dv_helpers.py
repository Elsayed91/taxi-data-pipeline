import os
import yaml
from typing import Any


class ValidationError(Exception):
    """Validation Unsuccessful"""


class ConfigLoader:
    """
    A class for loading and parsing YAML configuration files,
    substituting the values of environmental variables.
    The variables must match the format ${VARIABLE} to be substituted.
    Usage Example: config = ConfigLoader("/path/to/yaml").load_config()
    """

    def __init__(self, config_path: str):
        self.config_path = config_path

    def substitute_env_variables(self, data):
        """
        Recursively substitutes the values of environmental variables
        in the given data structure.

        Args:
            data: The data structure to process. Can be a dictionary, list, or string.

        Returns:
            The data structure with the environmental variables substituted.
        """
        if isinstance(data, dict):
            for key, value in data.items():
                data[key] = self.substitute_env_variables(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                data[i] = self.substitute_env_variables(item)
        elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            # This is an environmental variable. Substitute its value.
            var_name = data[2:-1]
            data = os.getenv(var_name)
        return data

    def load_config(self):
        """
        Loads and parses the YAML configuration file,
        substituting the values of environmental variables.

        Returns:
            The parsed configuration data with the environmental variables substituted.
        """
        # Load the YAML file
        with open(self.config_path, "r") as f:
            data = yaml.safe_load(f)

        # Substitute the values of the environmental variables
        self.substitute_env_variables(data)

        return data

    def write_config(self, output_path: str):
        """
        Writes the processed values out to a new YAML file,
        with environmental variables substituted.

        Args:
            output_path: The path to write the YAML file to.

        Returns:
            None
        """
        data = self.load_config()

        # Open the output file in write mode
        with open(output_path, "w") as f:
            # Use the yaml.dump() function to write the dictionary to the YAML file
            yaml.dump(data, f)


def retrieve_nested_value(mapping: dict[str, Any], key_of_interest: str) -> Any:
    """Retrieve the value associated with the given key in the nested mapping.

    Args:
        mapping (dict[str, Any]): The nested mapping to search in.
        key_of_interest (str): The key to look up.

    Yields:
        Any: The value associated with the given key in the nested mapping.
    """
    mappings = [mapping]
    while mappings:
        mapping = mappings.pop()
        try:
            items = mapping.items()
        except AttributeError:
            # we didn't store a mapping earlier on so just skip that value
            continue

        for key, value in items:
            if key == key_of_interest:
                yield value
            else:
                # type of the value will be checked in the next loop
                mappings.append(value)
