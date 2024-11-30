"""
Tests for Learning-Core-based Content Libraries
"""
from contextlib import contextmanager
from io import BytesIO
from urllib.parse import urlencode

from organizations.models import Organization
from rest_framework.test import APITransactionTestCase, APIClient

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content_libraries.constants import ALL_RIGHTS_RESERVED
from openedx.core.djangolib.testing.utils import skip_unless_cms

# Define the URLs here - don't use reverse() because we want to detect
# backwards-incompatible changes like changed URLs.
URL_PREFIX = '/api/libraries/v2/'
URL_LIB_CREATE = URL_PREFIX
URL_LIB_LIST = URL_PREFIX + '?{query_params}'
URL_LIB_DETAIL = URL_PREFIX + '{lib_key}/'  # Get data about a library, update or delete library
URL_LIB_BLOCK_TYPES = URL_LIB_DETAIL + 'block_types/'  # Get the list of XBlock types that can be added to this library
URL_LIB_LINKS = URL_LIB_DETAIL + 'links/'  # Get the list of links in this library, or add a new one
URL_LIB_COMMIT = URL_LIB_DETAIL + 'commit/'  # Commit (POST) or revert (DELETE) all pending changes to this library
URL_LIB_BLOCKS = URL_LIB_DETAIL + 'blocks/'  # Get the list of XBlocks in this library, or add a new one
URL_LIB_TEAM = URL_LIB_DETAIL + 'team/'  # Get the list of users/groups authorized to use this library
URL_LIB_TEAM_USER = URL_LIB_TEAM + 'user/{username}/'  # Add/edit/remove a user's permission to use this library
URL_LIB_TEAM_GROUP = URL_LIB_TEAM + 'group/{group_name}/'  # Add/edit/remove a group's permission to use this library
URL_LIB_PASTE_CLIPBOARD = URL_LIB_DETAIL + 'paste_clipboard/'  # Paste user clipboard (POST) containing Xblock data
URL_LIB_BLOCK = URL_PREFIX + 'blocks/{block_key}/'  # Get data about a block, or delete it
URL_LIB_BLOCK_PUBLISH = URL_LIB_BLOCK + 'publish/'  # Publish changes from a specified XBlock
URL_LIB_BLOCK_OLX = URL_LIB_BLOCK + 'olx/'  # Get or set the OLX of the specified XBlock
URL_LIB_BLOCK_ASSETS = URL_LIB_BLOCK + 'assets/'  # List the static asset files of the specified XBlock
URL_LIB_BLOCK_ASSET_FILE = URL_LIB_BLOCK + 'assets/{file_name}'  # Get, delete, or upload a specific static asset file

URL_LIB_LTI_PREFIX = URL_PREFIX + 'lti/1.3/'
URL_LIB_LTI_JWKS = URL_LIB_LTI_PREFIX + 'pub/jwks/'
URL_LIB_LTI_LAUNCH = URL_LIB_LTI_PREFIX + 'launch/'

URL_BLOCK_RENDER_VIEW = '/api/xblock/v2/xblocks/{block_key}/view/{view_name}/'
URL_BLOCK_EMBED_VIEW = '/xblocks/v2/{block_key}/embed/{view_name}/'  # Returns HTML not JSON so its URL is different
URL_BLOCK_GET_HANDLER_URL = '/api/xblock/v2/xblocks/{block_key}/handler_url/{handler_name}/'
URL_BLOCK_METADATA_URL = '/api/xblock/v2/xblocks/{block_key}/'
URL_BLOCK_FIELDS_URL = '/api/xblock/v2/xblocks/{block_key}/fields/'
URL_BLOCK_XBLOCK_HANDLER = '/api/xblock/v2/xblocks/{block_key}/handler/{user_id}-{secure_token}/{handler_name}/'


@skip_unless_cms  # Content Libraries REST API is only available in Studio
class ContentLibrariesRestApiTest(APITransactionTestCase):
    """
    Base class for Learning-Core-based Content Libraries test that use the REST API

    These tests use the REST API, which in turn relies on the Python API.
    Some tests may use the python API directly if necessary to provide
    coverage of any code paths not accessible via the REST API.

    In general, these tests should
    (1) Use public APIs only - don't directly create data using other methods,
        which results in a less realistic test and ties the test suite too
        closely to specific implementation details.
        (Exception: users can be provisioned using a user factory)
    (2) Assert that fields are present in responses, but don't assert that the
        entire response has some specific shape. That way, things like adding
        new fields to an API response, which are backwards compatible, won't
        break any tests, but backwards-incompatible API changes will.

    WARNING: every test should have a unique library slug, because even though
    the django/mysql database gets reset for each test case, the lookup between
    library slug and bundle UUID does not because it's assumed to be immutable
    and cached forever.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(username="Bob", email="bob@example.com", password="edx")
        # Create an organization
        self.organization, _ = Organization.objects.get_or_create(
            short_name="CL-TEST",
            defaults={"name": "Content Libraries Tachyon Exploration & Survey Team"},
        )
        self.clients_by_user = {}
        self.client.login(username=self.user.username, password="edx")

    # Assertions

    def assertDictContainsEntries(self, big_dict, subset_dict):
        """
        Assert that the first dict contains at least all of the same entries as
        the second dict.
        """
        for key, value in subset_dict.items():
            assert key in big_dict, f"Missing key: {key}"
            assert big_dict[key] == value, f"Value for key {key} does not match: expected {value}, got {big_dict[key]}"

    def assertOrderEqual(self, libraries_list, expected_order):
        """
        Assert that the provided list of libraries match the order of expected
        list by comparing the slugs.
        """
        assert [lib["slug"] for lib in libraries_list] == expected_order

    # API helpers

    def _api(self, method, url, data, expect_response):
        """
        Call a REST API
        """
        response = getattr(self.client, method)(url, data, format="json")
        assert response.status_code == expect_response,\
            'Unexpected response code {}:\n{}'.format(response.status_code, getattr(response, 'data', '(no data)'))
        return response.data

    @contextmanager
    def as_user(self, user):
        """
        Context manager to call the REST API as a user other than self.user
        """
        old_client = self.client
        if user not in self.clients_by_user:
            client = self.clients_by_user[user] = APIClient()
            client.force_authenticate(user=user)
        self.client = self.clients_by_user[user]  # pylint: disable=attribute-defined-outside-init
        yield
        self.client = old_client  # pylint: disable=attribute-defined-outside-init

    def _create_library(
        self, slug, title, description="", org=None,
        license_type=ALL_RIGHTS_RESERVED, expect_response=200,
    ):
        """ Create a library """
        if org is None:
            org = self.organization.short_name
        return self._api('post', URL_LIB_CREATE, {
            "org": org,
            "slug": slug,
            "title": title,
            "description": description,
            "license": license_type,
        }, expect_response)

    def _list_libraries(self, query_params_dict=None, expect_response=200):
        """ List libraries """
        if query_params_dict is None:
            query_params_dict = {}
        return self._api('get', URL_LIB_LIST.format(query_params=urlencode(query_params_dict)), None, expect_response)

    def _get_library(self, lib_key, expect_response=200):
        """ Get a library """
        return self._api('get', URL_LIB_DETAIL.format(lib_key=lib_key), None, expect_response)

    def _update_library(self, lib_key, expect_response=200, **data):
        """ Update an existing library """
        return self._api('patch', URL_LIB_DETAIL.format(lib_key=lib_key), data, expect_response)

    def _delete_library(self, lib_key, expect_response=200):
        """ Delete an existing library """
        return self._api('delete', URL_LIB_DETAIL.format(lib_key=lib_key), None, expect_response)

    def _get_library_links(self, lib_key):
        """ Get the links of the specified content library """
        return self._api('get', URL_LIB_LINKS.format(lib_key=lib_key), None, expect_response=200)

    def _link_to_library(self, lib_key, link_id, other_library_key, version=None):
        """
        Modify the library identified by lib_key to create a named link to
        other_library_key. This allows you to use XBlocks from other_library in
        lib. Optionally specify a version to link to.
        """
        data = {
            "id": link_id,
            "opaque_key": other_library_key,
            "version": version,
        }
        return self._api('post', URL_LIB_LINKS.format(lib_key=lib_key), data, expect_response=200)

    def _commit_library_changes(self, lib_key, expect_response=200):
        """ Commit changes to an existing library """
        return self._api('post', URL_LIB_COMMIT.format(lib_key=lib_key), None, expect_response)

    def _revert_library_changes(self, lib_key, expect_response=200):
        """ Revert pending changes to an existing library """
        return self._api('delete', URL_LIB_COMMIT.format(lib_key=lib_key), None, expect_response)

    def _get_library_team(self, lib_key, expect_response=200):
        """ Get the list of users/groups authorized to use this library """
        return self._api('get', URL_LIB_TEAM.format(lib_key=lib_key), None, expect_response)

    def _get_user_access_level(self, lib_key, username, expect_response=200):
        """ Fetch a user's access level """
        url = URL_LIB_TEAM_USER.format(lib_key=lib_key, username=username)
        return self._api('get', url, None, expect_response)

    def _add_user_by_email(self, lib_key, email, access_level, expect_response=200):
        """ Add a user of a specified permission level by their email address. """
        url = URL_LIB_TEAM.format(lib_key=lib_key)
        return self._api('post', url, {"access_level": access_level, "email": email}, expect_response)

    def _set_user_access_level(self, lib_key, username, access_level, expect_response=200):
        """ Change the specified user's access level """
        url = URL_LIB_TEAM_USER.format(lib_key=lib_key, username=username)
        return self._api('put', url, {"access_level": access_level}, expect_response)

    def _remove_user_access(self, lib_key, username, expect_response=200):
        """ Should effectively be the same as the above with access_level=None, but using the delete HTTP verb. """
        url = URL_LIB_TEAM_USER.format(lib_key=lib_key, username=username)
        return self._api('delete', url, None, expect_response)

    def _set_group_access_level(self, lib_key, group_name, access_level, expect_response=200):
        """ Change the specified group's access level """
        url = URL_LIB_TEAM_GROUP.format(lib_key=lib_key, group_name=group_name)
        if access_level is None:
            return self._api('delete', url, None, expect_response)
        else:
            return self._api('put', url, {"access_level": access_level}, expect_response)

    def _get_library_block_types(self, lib_key, expect_response=200):
        """ Get the list of permitted XBlocks for this library """
        return self._api('get', URL_LIB_BLOCK_TYPES.format(lib_key=lib_key), None, expect_response)

    def _get_library_blocks(self, lib_key, query_params_dict=None, expect_response=200):
        """ Get the list of XBlocks in the library """
        if query_params_dict is None:
            query_params_dict = {}
        return self._api(
            'get',
            URL_LIB_BLOCKS.format(lib_key=lib_key) + '?' + urlencode(query_params_dict, doseq=True),
            None,
            expect_response
        )

    def _add_block_to_library(self, lib_key, block_type, slug, parent_block=None, expect_response=200):
        """ Add a new XBlock to the library """
        data = {"block_type": block_type, "definition_id": slug}
        if parent_block:
            data["parent_block"] = parent_block
        return self._api('post', URL_LIB_BLOCKS.format(lib_key=lib_key), data, expect_response)

    def _get_library_block(self, block_key, expect_response=200):
        """ Get a specific block in the library """
        return self._api('get', URL_LIB_BLOCK.format(block_key=block_key), None, expect_response)

    def _delete_library_block(self, block_key, expect_response=200):
        """ Delete a specific block from the library """
        self._api('delete', URL_LIB_BLOCK.format(block_key=block_key), None, expect_response)

    def _get_library_block_olx(self, block_key, expect_response=200):
        """ Get the OLX of a specific block in the library """
        result = self._api('get', URL_LIB_BLOCK_OLX.format(block_key=block_key), None, expect_response)
        if expect_response == 200:
            return result["olx"]
        return result

    def _set_library_block_olx(self, block_key, new_olx, expect_response=200):
        """ Overwrite the OLX of a specific block in the library """
        return self._api('post', URL_LIB_BLOCK_OLX.format(block_key=block_key), {"olx": new_olx}, expect_response)

    def _get_library_block_assets(self, block_key, expect_response=200):
        """ List the static asset files belonging to the specified XBlock """
        url = URL_LIB_BLOCK_ASSETS.format(block_key=block_key)
        result = self._api('get', url, None, expect_response)
        return result["files"] if expect_response == 200 else result

    def _get_library_block_asset(self, block_key, file_name, expect_response=200):
        """
        Get metadata about one static asset file belonging to the specified
        XBlock.
        """
        url = URL_LIB_BLOCK_ASSET_FILE.format(block_key=block_key, file_name=file_name)
        return self._api('get', url, None, expect_response)

    def _set_library_block_asset(self, block_key, file_name, content, expect_response=200):
        """
        Set/replace a static asset file belonging to the specified XBlock.

        content should be a binary string.
        """
        assert isinstance(content, bytes)
        file_handle = BytesIO(content)
        url = URL_LIB_BLOCK_ASSET_FILE.format(block_key=block_key, file_name=file_name)
        response = self.client.put(url, data={"content": file_handle})
        assert response.status_code == expect_response,\
            'Unexpected response code {}:\n{}'.format(response.status_code, getattr(response, 'data', '(no data)'))

    def _delete_library_block_asset(self, block_key, file_name, expect_response=204):
        """ Delete a static asset file. """
        url = URL_LIB_BLOCK_ASSET_FILE.format(block_key=block_key, file_name=file_name)
        return self._api('delete', url, None, expect_response)

    def _publish_library_block(self, block_key, expect_response=200):
        """ Publish changes from a specified XBlock """
        return self._api('post', URL_LIB_BLOCK_PUBLISH.format(block_key=block_key), None, expect_response)

    def _paste_clipboard_content_in_library(self, lib_key, block_id, expect_response=200):
        """ Paste's the users clipboard content into Library """
        url = URL_LIB_PASTE_CLIPBOARD.format(lib_key=lib_key)
        data = {"block_id": block_id}
        return self._api('post', url, data, expect_response)

    def _render_block_view(self, block_key, view_name, version=None, expect_response=200):
        """
        Render an XBlock's view in the active application's runtime.
        Note that this endpoint has different behavior in Studio (draft mode)
        vs. the LMS (published version only).
        """
        if version is not None:
            block_key += f"@{version}"
        url = URL_BLOCK_RENDER_VIEW.format(block_key=block_key, view_name=view_name)
        return self._api('get', url, None, expect_response)

    def _embed_block(
        self,
        block_key,
        *,
        view_name="student_view",
        version: str | int | None = None,
        expect_response=200,
    ) -> str:
        """
        Get an HTML response that displays the given XBlock. Returns HTML.
        """
        url = URL_BLOCK_EMBED_VIEW.format(block_key=block_key, view_name=view_name)
        if version is not None:
            url += f"?version={version}"
        response = self.client.get(url)
        assert response.status_code == expect_response, 'Unexpected response code {}:'.format(response.status_code)
        return response.content.decode()

    def _get_block_handler_url(self, block_key, handler_name):
        """
        Get the URL to call a specific XBlock's handler.
        The URL itself encodes authentication information so can be called
        without session authentication or any other kind of authentication.
        """
        url = URL_BLOCK_GET_HANDLER_URL.format(block_key=block_key, handler_name=handler_name)
        return self._api('get', url, None, expect_response=200)["handler_url"]

    def _get_basic_xblock_metadata(self, block_key, version=None, expect_response=200):
        """ Get basic metadata about a specific block in the library. """
        if version is not None:
            block_key += f"@{version}"
        result = self._api('get', URL_BLOCK_METADATA_URL.format(block_key=block_key), None, expect_response)
        return result

    def _get_library_block_fields(self, block_key, version=None, expect_response=200):
        """ Get the fields of a specific block in the library. This API is only used by the MFE editors. """
        if version is not None:
            block_key += f"@{version}"
        result = self._api('get', URL_BLOCK_FIELDS_URL.format(block_key=block_key), None, expect_response)
        return result

    def _set_library_block_fields(self, block_key, new_fields, expect_response=200):
        """ Set the fields of a specific block in the library. This API is only used by the MFE editors. """
        return self._api('post', URL_BLOCK_FIELDS_URL.format(block_key=block_key), new_fields, expect_response)
