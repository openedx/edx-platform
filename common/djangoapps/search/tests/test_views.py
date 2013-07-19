"""
Basic test for views in search
"""

import django_future.csrf


class MockCsrfProtection(object):
    """
    A replacement for django's default csrf protection

    Has to be initialized here because the decorators will be applied as soon as a module is imported,
    which sadly means that standard patching doesn't work.
    """
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

django_future.csrf.ensure_csrf_cookie = MockCsrfProtection

import requests
from django.http import HttpRequest
from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock, patch

import search.views as views
from search.models import SearchResults
from search.es_requests import MongoIndexer
from mocks import StubServer, StubRequestHandler


def mock_render_to_response(template, context):
    """
    Stand-in for testing allowing a quick check
    """

    return context


def mock_get_course_with_access(*args):
    """
    Another testing stand-in for course authentication

    The purpose of this right now is to ensure that this method won't error in tests.
    """

    return "fake-course"


def mock_course_indexing(course):
    """
    This is a simple stand in for the course-indexing endpoint, just to ensure that transmission is smooth.
    """

    return course


class PersonalServer(StubServer):
    """
    SubServer implementation for simple search mocking
    """

    def log_request(self, request_type, path, content):
        self.requests.append(self.request(request_type, path, content))
        if path.endswith("_search"):
            self.content = "{}"


class MockMongoIndexer(MongoIndexer):

    def __init__(self):
        pass

    def index_course(self, course):
        return course


@override_settings(ES_DATABASE="http://127.0.0.1:9203")
@patch('search.views.render_to_response', Mock(side_effect=mock_render_to_response, autospec=True))
@patch('search.views.get_course_with_access', Mock(side_effect=mock_get_course_with_access, autospec=True))
class ViewTest(TestCase):
    """
    Basic test class for base view case. A small test, but one that adresses some blind spots
    """

    def setUp(self):
        self.stub = PersonalServer(StubRequestHandler, 9203)

    def test_basic_view(self):
        response = views._find(HttpRequest(), "org/test-course/run")
        self.assertTrue(isinstance(response, SearchResults))
        test = views._construct_search_context(response, 1, "all")
        self.assertEqual(set(test.keys()), set(["all", "video", "problem"]))
        self.assertFalse(bool(test["all"]["results"]))
        self.assertEqual(test["video"]["results"], {})

    def test_search_endpoint(self):
        request = HttpRequest()
        request.method = "GET"
        request.user = "fake-user"
        response = views.search(request, 'fake/course/id')
        self.assertTrue(isinstance(response['search_results']['all'], dict))
        self.assertEqual(response['search_results']['all']['total'], 0)

    @patch('search.views.MongoIndexer', Mock(side_effect=MockMongoIndexer, autospec=True))
    def test_index_course(self):
        request = HttpRequest()
        request.POST = {"course": "fake-course"}
        response = views.index_course(request)
        self.assertEqual(response.status_code, 204)
        self.assertTrue(response.has_header("content-type"))

    def tearDown(self):
        self.stub.stop()
