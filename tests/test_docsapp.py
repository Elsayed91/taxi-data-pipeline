from components.docs_app.docker.app import load_index
import pytest
from unittest.mock import patch


@pytest.mark.parametrize(
    "bucket, index_path, expected",
    [
        ("my-bucket", "path/to/index.txt", b"This is the contents of the index file."),
        (
            "my-bucket",
            "path/to/index2.txt",
            b"This is the contents of another index file.",
        ),
    ],
)
@patch("gcsfs.GCSFileSystem")
def test_load_index(mock_gcsfs, bucket, index_path, expected):

    mock_fs = mock_gcsfs.return_value
    mock_open = mock_fs.open
    mock_file = mock_open.return_value.__enter__.return_value
    mock_file.read.return_value = expected
    result = load_index(bucket, index_path)

    assert result == expected


@patch("gcsfs.GCSFileSystem")
def test_load_index_exception(mock_gcsfs):
    mock_fs = mock_gcsfs.return_value
    mock_open = mock_fs.open
    mock_open.side_effect = Exception("Error opening file")

    with pytest.raises(Exception) as e:
        result = load_index("invalid-bucket", "invalid-path")
        assert str(e.value) == "Error opening file"
        assert (
            result
            == "<p>couldn't get index page. maybe you have not created it yet?</p>"
        )
