"""
Tests Library Collections REST API views
"""

from __future__ import annotations

from openedx_learning.api.authoring_models import Collection

from openedx.core.djangolib.testing.utils import skip_unless_cms
from openedx.core.djangoapps.content_libraries.tests.base import ContentLibrariesRestApiTest
from openedx.core.djangoapps.content_libraries.models import ContentLibrary
from common.djangoapps.student.tests.factories import UserFactory

URL_PREFIX = '/api/libraries/v2/{lib_key}/'
URL_LIB_COLLECTIONS = URL_PREFIX + 'collections/'
URL_LIB_COLLECTION = URL_LIB_COLLECTIONS + '{collection_id}/'


@skip_unless_cms  # Content Library Collections REST API is only available in Studio
class ContentLibraryCollectionsViewsTest(ContentLibrariesRestApiTest):
    """
    Tests for Content Library Collection REST API Views
    """

    def setUp(self):
        super().setUp()

        # Create Content Libraries
        self._create_library("test-lib-col-1", "Test Library 1")
        self._create_library("test-lib-col-2", "Test Library 2")
        self.lib1 = ContentLibrary.objects.get(slug="test-lib-col-1")
        self.lib2 = ContentLibrary.objects.get(slug="test-lib-col-2")

        print("self.lib1", self.lib1)
        print("self.lib2", self.lib2)

        # Create Content Library Collections
        self.col1 = Collection.objects.create(
            learning_package_id=self.lib1.learning_package.id,
            title="Collection 1",
            description="Description for Collection 1",
            created_by=self.user,
        )
        self.col2 = Collection.objects.create(
            learning_package_id=self.lib1.learning_package.id,
            title="Collection 2",
            description="Description for Collection 2",
            created_by=self.user,
        )
        self.col3 = Collection.objects.create(
            learning_package_id=self.lib2.learning_package.id,
            title="Collection 3",
            description="Description for Collection 3",
            created_by=self.user,
        )

    def test_get_library_collection(self):
        """
        Test retrieving a Content Library Collection
        """
        resp = self.client.get(
            URL_LIB_COLLECTION.format(lib_key=self.lib2.library_key, collection_id=self.col3.id)
        )

        # Check that correct Content Library Collection data retrieved
        expected_collection = {
            "title": "Collection 3",
            "description": "Description for Collection 3",
        }
        assert resp.status_code == 200
        self.assertDictContainsEntries(resp.data, expected_collection)

        # Check that a random user without permissions cannot access Content Library Collection
        random_user = UserFactory.create(username="Random", email="random@example.com")
        with self.as_user(random_user):
            resp = self.client.get(
                URL_LIB_COLLECTION.format(lib_key=self.lib2.library_key, collection_id=self.col3.id)
            )
            assert resp.status_code == 403

    def test_list_library_collections(self):
        """
        Test listing Content Library Collections
        """
        resp = self.client.get(URL_LIB_COLLECTIONS.format(lib_key=self.lib1.library_key))

        # Check that the correct collections are listed
        assert resp.status_code == 200
        assert len(resp.data) == 2
        expected_collections = [
            {"title": "Collection 1", "description": "Description for Collection 1"},
            {"title": "Collection 2", "description": "Description for Collection 2"},
        ]
        for collection, expected in zip(resp.data, expected_collections):
            self.assertDictContainsEntries(collection, expected)

        # Check that a random user without permissions cannot access Content Library Collections
        random_user = UserFactory.create(username="Random", email="random@example.com")
        with self.as_user(random_user):
            resp = self.client.get(URL_LIB_COLLECTIONS.format(lib_key=self.lib1.library_key))
            assert resp.status_code == 403

    def test_create_library_collection(self):
        """
        Test creating a Content Library Collection
        """
        post_data = {
            "title": "Collection 4",
            "description": "Description for Collection 4",
        }
        resp = self.client.post(
            URL_LIB_COLLECTIONS.format(lib_key=self.lib1.library_key), post_data, format="json"
        )

        # Check that the new Content Library Collection is returned in response and created in DB
        assert resp.status_code == 200
        self.assertDictContainsEntries(resp.data, post_data)

        created_collection = Collection.objects.get(id=resp.data["id"])
        self.assertIsNotNone(created_collection)

        # Check that user with read only access cannot create new Content Library Collection
        reader = UserFactory.create(username="Reader", email="reader@example.com")
        self._add_user_by_email(self.lib1.library_key, reader.email, access_level="read")

        with self.as_user(reader):
            post_data = {
                "title": "Collection 5",
                "description": "Description for Collection 5",
            }
            resp = self.client.post(
                URL_LIB_COLLECTIONS.format(lib_key=self.lib1.library_key), post_data, format="json"
            )

            assert resp.status_code == 403

    def test_update_library_collection(self):
        """
        Test updating a Content Library Collection
        """
        patch_data = {
            "title": "Collection 3 Updated",
        }
        resp = self.client.patch(
            URL_LIB_COLLECTION.format(lib_key=self.lib2.library_key, collection_id=self.col3.id),
            patch_data,
            format="json"
        )

        # Check that updated Content Library Collection is returned in response and updated in DB
        assert resp.status_code == 200
        self.assertDictContainsEntries(resp.data, patch_data)

        created_collection = Collection.objects.get(id=resp.data["id"])
        self.assertIsNotNone(created_collection)
        self.assertEqual(created_collection.title, patch_data["title"])

        # Check that user with read only access cannot update a Content Library Collection
        reader = UserFactory.create(username="Reader", email="reader@example.com")
        self._add_user_by_email(self.lib1.library_key, reader.email, access_level="read")

        with self.as_user(reader):
            patch_data = {
                "title": "Collection 3 should not update",
            }
            resp = self.client.patch(
                URL_LIB_COLLECTION.format(lib_key=self.lib2.library_key, collection_id=self.col3.id),
                patch_data,
                format="json"
            )

            assert resp.status_code == 403

    def test_delete_library_collection(self):
        """
        Test deleting a Content Library Collection

        Note: Currently not implemented and should return a 405
        """
        resp = self.client.delete(
            URL_LIB_COLLECTION.format(lib_key=self.lib2.library_key, collection_id=self.col3.id)
        )

        assert resp.status_code == 405
