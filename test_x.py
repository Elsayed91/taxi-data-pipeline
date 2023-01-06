import pytest
from unittest.mock import patch
import gcsfs
from components.ge.data_validation import *
import mock


@pytest.fixture
def mock_spark_session():
    with mock.patch("components.ge.data_validation.SparkSession") as mock_spark_session:
        yield mock_spark_session


@pytest.fixture
def mock_config_loader():
    with mock.patch("components.ge.helpers.ConfigLoader") as mock_config_loader:
        yield mock_config_loader


@pytest.fixture
def mock_base_data_context():
    with mock.patch(
        "components.ge.data_validation.BaseDataContext"
    ) as mock_base_data_context:
        yield mock_base_data_context


@pytest.fixture
def mock_run_checkpoint():
    with mock.patch(
        "components.ge.data_validation.run_checkpoint"
    ) as mock_run_checkpoint:
        yield mock_run_checkpoint


@pytest.fixture
def mock_build_data_docs():
    with mock.patch(
        "components.ge.data_validation.build_data_docs"
    ) as mock_build_data_docs:
        yield mock_build_data_docs


def test_main(
    mock_spark_session,
    mock_config_loader,
    mock_base_data_context,
    mock_run_checkpoint,
    mock_build_data_docs,
):
    # Set up the mock SparkSession
    mock_spark_session.builder.getOrCreate.return_value = mock_spark_session

    # Set up the mock ConfigLoader objects
    mock_ge_config_loader = mock_config_loader.return_value
    mock_ge_config_loader.load_config.return_value = {"ge_config": "value"}
    mock_cp_config_loader = mock_config_loader.return_value
    mock_cp_config_loader.load_config.return_value = {"cp_config": "value"}

    # Set up the mock BaseDataContext object
    mock_data_context = mock_base_data_context.return_value
    mock_data_context.add_checkpoint.return_value = None

    # Set up the mock run_checkpoint method
    mock_run_checkpoint.return_value = {"success_percent": 0.75}

    # Set up the mock build_data_docs method
    mock_build_data_docs.return_value = None

    # Call the main function
    main()

    # Assert that the necessary objects and methods were called
    def test_main(
        mock_spark_session,
        mock_config_loader,
        mock_base_data_context,
        mock_run_checkpoint,
        mock_build_data_docs,
    ):
        # Set up the mock SparkSession
        mock_spark_session.builder.getOrCreate.return_value = mock_spark_session

        # Set up the mock ConfigLoader objects
        mock_ge_config_loader = mock_config_loader.return_value
        mock_ge_config_loader.load_config.return_value = {"ge_config": "value"}
        mock_cp_config_loader = mock_config_loader.return_value
        mock_cp_config_loader.load_config.return_value = {"cp_config": "value"}

        # Set up the mock BaseDataContext object
        mock_data_context = mock_base_data_context.return_value
        mock_data_context.add_checkpoint.return_value = None

        # Set up the mock run_checkpoint method
        mock_run_checkpoint.return_value = {"success_percent": 0.75}

        # Set up the mock build_data_docs method
        mock_build_data_docs.return_value = None

        # Call the main function
        main()

        # Assert that the necessary objects and methods were called
        mock_spark_session.builder.getOrCreate.assert_called_once()
        mock_ge_config_loader.load_config.assert_called_once_with(GE_CONFIG_PATH)
        mock_cp_config_loader.load_config.assert_called_once_with(CP_CONFIG_PATH)
        mock_base_data_context.assert_called_once_with({"ge_config": "value"})
        mock_data_context.add_checkpoint.assert_called_once_with({"cp_config": "value"})
        mock_run_checkpoint.assert_called_once_with(
            mock_data_context, checkpoint_name="cp"
        )
        mock_build_data_docs.assert_called_once_with(mock_data_context)
