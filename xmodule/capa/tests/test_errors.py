"""
Unit tests for custom error handling in the XQueue submission interface.
"""

import pytest
from xmodule.capa.errors import (
    JSONParsingError,
    MissingKeyError,
    ValidationError,
    TypeErrorSubmission,
    RuntimeErrorSubmission,
    GetSubmissionParamsError
)


def test_json_parsing_error():
    with pytest.raises(JSONParsingError) as excinfo:
        raise JSONParsingError("test_name", "test_error")
    assert str(excinfo.value) == "Error parsing test_name: test_error"


def test_missing_key_error():
    with pytest.raises(MissingKeyError) as excinfo:
        raise MissingKeyError("test_key")
    assert str(excinfo.value) == "Missing key: test_key"


def test_validation_error():
    with pytest.raises(ValidationError) as excinfo:
        raise ValidationError("test_error")
    assert str(excinfo.value) == "Validation error: test_error"


def test_type_error_submission():
    with pytest.raises(TypeErrorSubmission) as excinfo:
        raise TypeErrorSubmission("test_error")
    assert str(excinfo.value) == "Type error: test_error"


def test_runtime_error_submission():
    with pytest.raises(RuntimeErrorSubmission) as excinfo:
        raise RuntimeErrorSubmission("test_error")
    assert str(excinfo.value) == "Runtime error: test_error"


def test_get_submission_params_error_default():
    """Test GetSubmissionParamsError with default message."""
    with pytest.raises(GetSubmissionParamsError) as excinfo:
        raise GetSubmissionParamsError()
    assert str(excinfo.value) == "Submission parameters error: Block instance is not defined!"


def test_get_submission_params_error_custom():
    """Test GetSubmissionParamsError with a custom error message."""
    with pytest.raises(GetSubmissionParamsError) as excinfo:
        raise GetSubmissionParamsError("Custom error message")
    assert str(excinfo.value) == "Submission parameters error: Custom error message"
