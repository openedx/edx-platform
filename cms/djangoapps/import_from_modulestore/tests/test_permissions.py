"""
Test the permissions module for the import_from_modulestore app.
"""

from unittest.mock import MagicMock
import uuid

from django.http.response import Http404
from django.test import TestCase

from common.djangoapps.student.tests.factories import UserFactory
from cms.djangoapps.import_from_modulestore.permissions import IsImportAuthor
from .factories import ImportFactory


class TestIsImportAuthorPermission(TestCase):
    """
    Test the IsImportAuthor permission class.
    """

    def setUp(self):
        """
        Create a user and an import object for testing.
        """
        self.user = UserFactory()
        self.import_event = ImportFactory(user=self.user)
        self.permission = IsImportAuthor()
        self.request = MagicMock()
        self.request.data = {'import_uuid': str(self.import_event.uuid)}

    def test_has_permission_author(self):
        """
        Test that the author of the import has permission.
        """
        self.request.user = self.user
        self.assertTrue(self.permission.has_permission(self.request, None))

    def test_has_permission_non_author(self):
        """
        Test that a non-author does not have permission.
        """
        other_user = UserFactory()
        self.request.user = other_user
        self.assertFalse(self.permission.has_permission(self.request, None))

    def test_has_permission_no_import(self):
        """
        Test that a user without an import does not have permission.
        """
        self.request.user = self.user
        self.request.data = {'import_uuid': str(uuid.uuid4())}
        self.assertRaises(
            Http404,
            self.permission.has_permission,
            self.request,
            None
        )
