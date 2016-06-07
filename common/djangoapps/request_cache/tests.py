"""
Tests for the request cache.
"""
from celery.task import task
from django.conf import settings
from django.test import TestCase

from request_cache import get_request_or_stub
from xmodule.modulestore.django import modulestore


class TestRequestCache(TestCase):
    """
    Tests for the request cache.
    """

    def test_get_request_or_stub(self):
        """
        Outside the context of the request, we should still get a request
        that allows us to build an absolute URI.
        """
        stub = get_request_or_stub()
        expected_url = "http://{site_name}/foobar".format(site_name=settings.SITE_NAME)
        self.assertEqual(stub.build_absolute_uri("foobar"), expected_url)

    @task
    def _dummy_task(self):
        """ Create a task that adds stuff to the request cache. """
        cache = {"course_cache": "blah blah blah"}
        modulestore().request_cache.data.update(cache)

    def test_clear_cache_celery(self):
        """ Test that the request cache is cleared after a task is run. """
        self._dummy_task.apply(args=(self,)).get()
        self.assertEqual(modulestore().request_cache.data, {})
