import os
import yaml
import pytest

from components.great_expectations.helpers import ConfigLoader, retrieve_nested_value


@pytest.fixture
def config_data():
    return {
        "key1": "${VAR1}",
        "key2": ["${VAR2}", "${VAR3}"],
        "key3": {"key4": "${VAR4}", "key5": "${VAR5}"},
    }


@pytest.fixture
def env_vars():
    return {
        "VAR1": "value1",
        "VAR2": "value2",
        "VAR3": "value3",
        "VAR4": "value4",
        "VAR5": "value5",
    }


def test_substitute_env_variables(config_data, env_vars):
    # Set the environmental variables
    for var, value in env_vars.items():
        os.environ[var] = value

    # Create a ConfigLoader instance
    loader = ConfigLoader("dummy_path")

    # Substitute the environmental variables in the config data
    result = loader.substitute_env_variables(config_data)

    # Check that the environmental variables have been substituted
    assert result == {
        "key1": "value1",
        "key2": ["value2", "value3"],
        "key3": {"key4": "value4", "key5": "value5"},
    }


def test_load_config(mocker, config_data, env_vars):
    # Set the environmental variables
    for var, value in env_vars.items():
        os.environ[var] = value

    # Mock the `yaml.safe_load` function to return the config data
    mocker.patch("yaml.safe_load", return_value=config_data)
    mocker.patch("builtins.open", create=True)
    # Create a ConfigLoader instance
    loader = ConfigLoader("dummy_path")

    # Load the config
    result = loader.load_config()

    # Check that the environmental variables have been substituted
    assert result == {
        "key1": "value1",
        "key2": ["value2", "value3"],
        "key3": {"key4": "value4", "key5": "value5"},
    }


def test_retrieve_nested_value():
    mapping = {
        "key1": "value1",
        "key2": {"key3": "value3", "key4": "value4"},
        "key5": [{"key6": "value6"}, {"key7": "value7"}],
        "key8": [
            [{"key9": "value9"}],
            [{"key10": {"key12": "value12"}, "key11": "value11"}],
        ],
    }

    # Test retrieval of top-level key
    assert list(retrieve_nested_value(mapping, "key1")) == ["value1"]

    # Test retrieval of nested key
    assert list(retrieve_nested_value(mapping, "key3")) == ["value3"]

    # Test retrieval of key in list of mappings
    assert list(retrieve_nested_value(mapping, "key6")) == ["value6"]
    assert list(retrieve_nested_value(mapping, "key9")) == ["value9"]
    assert list(retrieve_nested_value(mapping, "key12")) == ["value12"]
