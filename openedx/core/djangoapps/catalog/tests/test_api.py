"""
Tests for the Catalog apps `api.py` functions.
"""
<<<<<<< HEAD
from mock import patch
=======
from unittest.mock import patch
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

from django.test import TestCase

from openedx.core.djangoapps.catalog.api import get_course_run_details
from openedx.core.djangoapps.catalog.tests.factories import CourseRunFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
class TestCatalogApi(TestCase):
    """
    Tests for the Catalog apps `api.py` functions.
    """

    @patch("openedx.core.djangoapps.catalog.api._get_course_run_details")
    def test_get_course_run_details(self, mock_get_course_run_details):
        """
        Test for Python API `get_course_run_details` function.
        """
        course_run = CourseRunFactory()

        mock_get_course_run_details.return_value = {
            'title': course_run['title'],
        }

        results = get_course_run_details(course_run['key'], ['title'])

        assert results['title'] == course_run['title']
