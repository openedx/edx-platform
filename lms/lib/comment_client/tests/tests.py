import logging

from django.test import TestCase
from django.contrib.auth.models import User, AnonymousUser
from mock import patch
from comment_client.utils import *
import comment_client as cc

log = logging.getLogger(__name__)

class CommentClientTest(TestCase):

    def test_from_django_user(self):
        """
        Simple test of the comment service User class' static
        factory method which expects a django.contrib.auth.models.User and
        returns a comment_client.User
        """
        with patch('student.models.cc.User.save'):
            user = User("fred","fred@edx.org")
            comment_user = cc.User.from_django_user(user)

    def test_from_django_user_anon(self):
        """
        Test for a production bug occurring when a user is passed to the
        static factory method in an unauthenticated contenxt.  The
        AnonymousUser class has no attribute email.  Working around this,
        doesn't make much sense, the first change is to raise an error if
        the object passed to from_django_user hasn't received a django user.
        The next step is to handle this case properly upstream.
        """
        with patch('student.models.cc.User.save'):
            # Test that the appropriate error is raised.
            anon = AnonymousUser()
            self.assertRaises(CommentClientError, cc.User.from_django_user, anon)