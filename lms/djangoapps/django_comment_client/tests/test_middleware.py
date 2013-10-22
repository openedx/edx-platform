from django.test import TestCase

import comment_client
import django.http
import django_comment_client.middleware as middleware


class AjaxExceptionTestCase(TestCase):

# TODO: check whether the correct error message is produced.
# The error message should be the same as the argument to CommentClientError
    def setUp(self):
        self.a = middleware.AjaxExceptionMiddleware()
        self.request1 = django.http.HttpRequest()
        self.request0 = django.http.HttpRequest()
        self.exception1 = comment_client.CommentClientError('{}')
        self.exception2 = comment_client.CommentClientError('Foo!')
        self.exception0 = ValueError()
        self.request1.META['HTTP_X_REQUESTED_WITH'] = "XMLHttpRequest"
        self.request0.META['HTTP_X_REQUESTED_WITH'] = "SHADOWFAX"

    def test_process_exception(self):
        response1 = self.a.process_exception(self.request1, self.exception1)
        self.assertIsInstance(response1, middleware.JsonError)
        self.assertEqual(500, response1.status_code)

        response2 = self.a.process_exception(self.request1, self.exception2)
        self.assertIsInstance(response2, middleware.JsonError)
        self.assertEqual(500, response2.status_code)

        self.assertIsNone(self.a.process_exception(self.request1, self.exception0))
        self.assertIsNone(self.a.process_exception(self.request0, self.exception1))
        self.assertIsNone(self.a.process_exception(self.request0, self.exception0))
