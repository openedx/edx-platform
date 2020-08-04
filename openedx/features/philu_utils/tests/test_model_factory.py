import pytest
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from openedx.features.philu_utils.model_factory import random_course_key


def test_random_course_key():
    try:
        course_key = random_course_key()
        assert isinstance(course_key, CourseKey)
    except InvalidKeyError as error:
        pytest.fail('Invalid course key; {error}'.format(error=error))
