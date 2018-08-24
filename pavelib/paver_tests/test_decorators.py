""" Tests for the utility decorators for Paver """
import time

import pytest

from pavelib.utils.decorators import (
    timeout, TimeoutException
)


def test_function_under_timeout():

    @timeout(1)
    def sample_function_1():
        time.sleep(0.1)
        return "sample text"

    value = sample_function_1()
    assert value == "sample text"


def test_function_over_timeout():

    @timeout(0.1)
    def sample_function_2():
        time.sleep(1)
        return "sample text"

    with pytest.raises(TimeoutException):
        sample_function_2()
