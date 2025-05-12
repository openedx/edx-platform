"""
Unit tests for /api/contentstore/v2/downstreams/* JSON APIs.
"""
import json
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from django.conf import settings
from django.urls import reverse
from freezegun import freeze_time
from organizations.models import Organization

from cms.djangoapps.contentstore.helpers import StaticFileNotices
from cms.lib.xblock.upstream_sync import BadUpstream, UpstreamLink
from cms.djangoapps.contentstore.tests.utils import CourseTestCase
from cms.djangoapps.contentstore.xblock_storage_handlers import view_handlers as xblock_view_handlers
from opaque_keys.edx.keys import UsageKey
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory

from .. import downstreams as downstreams_views

MOCK_UPSTREAM_ERROR = "your LibraryGPT subscription has expired"
URL_PREFIX = '/api/libraries/v2/'
URL_LIB_CREATE = URL_PREFIX
URL_LIB_BLOCKS = URL_PREFIX + '{lib_key}/blocks/'
URL_LIB_BLOCK_PUBLISH = URL_PREFIX + 'blocks/{block_key}/publish/'
URL_LIB_BLOCK_OLX = URL_PREFIX + 'blocks/{block_key}/olx/'


def _get_upstream_link_good_and_syncable(downstream):
    return UpstreamLink(
        upstream_ref=downstream.upstream,
        upstream_key=UsageKey.from_string(downstream.upstream),
        version_synced=downstream.upstream_version,
        version_available=(downstream.upstream_version or 0) + 1,
        version_declined=downstream.upstream_version_declined,
        error_message=None,
    )


def _get_upstream_link_bad(_downstream):
    raise BadUpstream(MOCK_UPSTREAM_ERROR)


class _BaseDownstreamViewTestMixin:
    """
    Shared data and error test cases.
    """
    def setUp(self):
        """
        Create a simple course with one unit and two videos, one of which is linked to an "upstream".
        """
        super().setUp()
        self.now = datetime.now(timezone.utc)
        freezer = freeze_time(self.now)
        self.addCleanup(freezer.stop)
        freezer.start()
        self.maxDiff = 2000

        self.organization, _ = Organization.objects.get_or_create(
            short_name="CL-TEST",
            defaults={"name": "Content Libraries Tachyon Exploration & Survey Team"},
        )
        self.superuser = UserFactory(username="superuser", password="password", is_staff=True, is_superuser=True)
        self.client.login(username=self.superuser.username, password="password")

        self.library_title = "Test Library 1"
        self.library_id = self._create_library(
            slug="testlib1_preview",
            title=self.library_title,
            description="Testing XBlocks"
        )["id"]
        self.html_lib_id = self._add_block_to_library(self.library_id, "html", "html-baz")["id"]
        self.video_lib_id = self._add_block_to_library(self.library_id, "video", "video-baz")["id"]
        self._publish_library_block(self.html_lib_id)
        self._publish_library_block(self.video_lib_id)
        self.mock_upstream_link = f"{settings.COURSE_AUTHORING_MICROFRONTEND_URL}/library/{self.library_id}/components?usageKey={self.video_lib_id}"  # pylint: disable=line-too-long  # noqa: E501
        self.course = CourseFactory.create()
        chapter = BlockFactory.create(category='chapter', parent=self.course)
        sequential = BlockFactory.create(category='sequential', parent=chapter)
        unit = BlockFactory.create(category='vertical', parent=sequential)
        self.regular_video_key = BlockFactory.create(category='video', parent=unit).usage_key
        self.downstream_video_key = BlockFactory.create(
            category='video', parent=unit, upstream=self.video_lib_id, upstream_version=1,
        ).usage_key
        self.downstream_html_key = BlockFactory.create(
            category='html', parent=unit, upstream=self.html_lib_id, upstream_version=1,
        ).usage_key

        self.another_course = CourseFactory.create(display_name="Another Course")
        another_chapter = BlockFactory.create(category="chapter", parent=self.another_course)
        another_sequential = BlockFactory.create(category="sequential", parent=another_chapter)
        another_unit = BlockFactory.create(category="vertical", parent=another_sequential)
        self.another_video_keys = []
        for _ in range(3):
            # Adds 3 videos linked to the same upstream
            self.another_video_keys.append(
                BlockFactory.create(
                    category="video",
                    parent=another_unit,
                    upstream=self.video_lib_id,
                    upstream_version=1
                ).usage_key
            )

        self.fake_video_key = self.course.id.make_usage_key("video", "NoSuchVideo")
        self.learner = UserFactory(username="learner", password="password")
        self._set_library_block_olx(self.html_lib_id, "<html><b>Hello world!</b></html>")
        self._publish_library_block(self.html_lib_id)
        self._publish_library_block(self.video_lib_id)
        self._publish_library_block(self.html_lib_id)

    def _api(self, method, url, data, expect_response):
        """
        Call a REST API
        """
        response = getattr(self.client, method)(url, data, format="json")
        assert response.status_code == expect_response,\
            'Unexpected response code {}:\n{}'.format(response.status_code, getattr(response, 'data', '(no data)'))
        return response.data

    def _create_library(
        self, slug, title, description="", org=None,
        license_type='', expect_response=200,
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

    def _add_block_to_library(self, lib_key, block_type, slug, parent_block=None, expect_response=200):
        """ Add a new XBlock to the library """
        data = {"block_type": block_type, "definition_id": slug}
        if parent_block:
            data["parent_block"] = parent_block
        return self._api('post', URL_LIB_BLOCKS.format(lib_key=lib_key), data, expect_response)

    def _publish_library_block(self, block_key, expect_response=200):
        """ Publish changes from a specified XBlock """
        return self._api('post', URL_LIB_BLOCK_PUBLISH.format(block_key=block_key), None, expect_response)

    def _set_library_block_olx(self, block_key, new_olx, expect_response=200):
        """ Overwrite the OLX of a specific block in the library """
        return self._api('post', URL_LIB_BLOCK_OLX.format(block_key=block_key), {"olx": new_olx}, expect_response)

    def call_api(self, usage_key_string):
        raise NotImplementedError


class SharedErrorTestCases(_BaseDownstreamViewTestMixin):
    """
    Shared error test cases.
    """
    def test_404_downstream_not_found(self):
        """
        Do we raise 404 if the specified downstream block could not be loaded?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.fake_video_key)
        assert response.status_code == 404
        assert "not found" in response.data["developer_message"]

    def test_404_downstream_not_accessible(self):
        """
        Do we raise 404 if the user lacks read access on the specified downstream block?
        """
        self.client.login(username="learner", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 404
        assert "not found" in response.data["developer_message"]


class GetDownstreamViewTest(SharedErrorTestCases, SharedModuleStoreTestCase):
    """
    Test that `GET /api/v2/contentstore/downstreams/...` inspects a downstream's link to an upstream.
    """
    def call_api(self, usage_key_string):
        return self.client.get(f"/api/contentstore/v2/downstreams/{usage_key_string}")

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    def test_200_good_upstream(self):
        """
        Does the happy path work?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 200
        assert response.data['upstream_ref'] == self.video_lib_id
        assert response.data['error_message'] is None
        assert response.data['ready_to_sync'] is True
        assert response.data['upstream_link'] == self.mock_upstream_link

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_bad)
    def test_200_bad_upstream(self):
        """
        If the upstream link is broken, do we still return 200, but with an error message in body?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 200
        assert response.data['upstream_ref'] == self.video_lib_id
        assert response.data['error_message'] == MOCK_UPSTREAM_ERROR
        assert response.data['ready_to_sync'] is False
        assert response.data['upstream_link'] is None

    def test_200_no_upstream(self):
        """
        If the upstream link is missing, do we still return 200, but with an error message in body?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.regular_video_key)
        assert response.status_code == 200
        assert response.data['upstream_ref'] is None
        assert "is not linked" in response.data['error_message']
        assert response.data['ready_to_sync'] is False
        assert response.data['upstream_link'] is None


class PutDownstreamViewTest(SharedErrorTestCases, SharedModuleStoreTestCase):
    """
    Test that `PUT /api/v2/contentstore/downstreams/...` edits a downstream's link to an upstream.
    """
    def call_api(self, usage_key_string, sync: str | None = None):
        return self.client.put(
            f"/api/contentstore/v2/downstreams/{usage_key_string}",
            data=json.dumps({
                "upstream_ref": str(self.video_lib_id),
                **({"sync": sync} if sync else {}),
            }),
            content_type="application/json",
        )

    @patch.object(downstreams_views, "fetch_customizable_fields_from_block")
    @patch.object(downstreams_views, "sync_library_content")
    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    def test_200_with_sync(self, mock_sync, mock_fetch):
        """
        Does the happy path work (with sync=True)?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(str(self.regular_video_key), sync='true')
        assert response.status_code == 200
        video_after = modulestore().get_item(self.regular_video_key)
        assert mock_sync.call_count == 1
        assert mock_fetch.call_count == 0
        assert video_after.upstream == self.video_lib_id

    @patch.object(downstreams_views, "fetch_customizable_fields_from_block")
    @patch.object(downstreams_views, "sync_library_content")
    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    def test_200_no_sync(self, mock_sync, mock_fetch):
        """
        Does the happy path work (with sync=False)?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.regular_video_key, sync='false')
        assert response.status_code == 200
        video_after = modulestore().get_item(self.regular_video_key)
        assert mock_sync.call_count == 0
        assert mock_fetch.call_count == 1
        assert video_after.upstream == self.video_lib_id

    @patch.object(
        downstreams_views, "fetch_customizable_fields_from_block", side_effect=BadUpstream(MOCK_UPSTREAM_ERROR),
    )
    def test_400(self, sync: str):
        """
        Do we raise a 400 if the provided upstream reference is malformed or not accessible?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 400
        assert MOCK_UPSTREAM_ERROR in response.data['developer_message']['upstream_ref']
        video_after = modulestore().get_item(self.regular_video_key)
        assert video_after.upstream is None


class DeleteDownstreamViewTest(SharedErrorTestCases, SharedModuleStoreTestCase):
    """
    Test that `DELETE /api/v2/contentstore/downstreams/...` severs a downstream's link to an upstream.
    """
    def call_api(self, usage_key_string):
        return self.client.delete(f"/api/contentstore/v2/downstreams/{usage_key_string}")

    @patch.object(downstreams_views, "sever_upstream_link")
    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    def test_204(self, mock_sever):
        """
        Does the happy path work?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 204
        assert mock_sever.call_count == 1

    @patch.object(downstreams_views, "sever_upstream_link")
    def test_204_no_upstream(self, mock_sever):
        """
        If there's no upsream, do we still happily return 204?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.regular_video_key)
        assert response.status_code == 204
        assert mock_sever.call_count == 1


class _DownstreamSyncViewTestMixin(SharedErrorTestCases):
    """
    Shared tests between the /api/contentstore/v2/downstreams/.../sync endpoints.
    """

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_bad)
    def test_400_bad_upstream(self):
        """
        If the upstream link is bad, do we get a 400?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 400
        assert MOCK_UPSTREAM_ERROR in response.data["developer_message"][0]

    def test_400_no_upstream(self):
        """
        If the upstream link is missing, do we get a 400?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.regular_video_key)
        assert response.status_code == 400
        assert "is not linked" in response.data["developer_message"][0]


class CreateDownstreamViewTest(CourseTestCase, _BaseDownstreamViewTestMixin, SharedModuleStoreTestCase):
    """
    Tests create new downstream blocks
    """
    def call_api_post(self, library_content_key, category):
        """
        Call the api to create a downstream block using
        `library_content_key` as upstream
        """
        data = {
            "parent_locator": str(self.course.location),
            "display_name": "Test block",
            "library_content_key": library_content_key,
            "category": category,
        }
        return self.client.post(
            reverse("xblock_handler"),
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_200(self):
        response = self.call_api_post(self.html_lib_id, "html")

        assert response.status_code == 200
        data = response.json()
        assert data["upstreamRef"] == self.html_lib_id

        usage_key = UsageKey.from_string(data["locator"])
        item = modulestore().get_item(usage_key)
        assert item.upstream == self.html_lib_id

    @patch("cms.djangoapps.contentstore.helpers._insert_static_files_into_downstream_xblock")
    @patch("cms.djangoapps.contentstore.helpers.content_staging_api.stage_xblock_temporarily")
    @patch("cms.djangoapps.contentstore.xblock_storage_handlers.view_handlers.sync_from_upstream_block")
    def test_200_video(self, mock_sync, mock_stage, mock_insert):
        mock_lib_block = MagicMock()
        mock_lib_block.runtime.get_block_assets.return_value = ['mocked_asset']
        mock_sync.return_value = mock_lib_block
        mock_stage.return_value = MagicMock()
        mock_insert.return_value = StaticFileNotices()

        response = self.call_api_post(self.video_lib_id, "video")

        assert response.status_code == 200
        data = response.json()
        assert data["upstreamRef"] == self.video_lib_id

        usage_key = UsageKey.from_string(data["locator"])
        item = modulestore().get_item(usage_key)
        assert item.upstream == self.video_lib_id
        assert item.edx_video_id is not None


class PostDownstreamSyncViewTest(_DownstreamSyncViewTestMixin, SharedModuleStoreTestCase):
    """
    Test that `POST /api/v2/contentstore/downstreams/.../sync` initiates a sync from the linked upstream.
    """
    def call_api(self, usage_key_string):
        return self.client.post(f"/api/contentstore/v2/downstreams/{usage_key_string}/sync")

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    @patch.object(xblock_view_handlers, "import_static_assets_for_library_sync", return_value=StaticFileNotices())
    @patch.object(downstreams_views, "clear_transcripts")
    def test_200(self, mock_import_staged_content, mock_clear_transcripts):
        """
        Does the happy path work?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 200
        assert mock_import_staged_content.call_count == 1
        assert mock_clear_transcripts.call_count == 1


class DeleteDownstreamSyncViewtest(
    _DownstreamSyncViewTestMixin,
    SharedModuleStoreTestCase,
):
    """
    Test that `DELETE /api/v2/contentstore/downstreams/.../sync` declines a sync from the linked upstream.
    """
    def call_api(self, usage_key_string):
        return self.client.delete(f"/api/contentstore/v2/downstreams/{usage_key_string}/sync")

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    @patch.object(downstreams_views, "decline_sync")
    def test_204(self, mock_decline_sync):
        """
        Does the happy path work?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 204
        assert mock_decline_sync.call_count == 1


class GetUpstreamViewTest(
    _BaseDownstreamViewTestMixin,
    SharedModuleStoreTestCase,
):
    """
    Test that `GET /api/v2/contentstore/downstreams?...` returns list of links based on the provided filter.
    """
    def call_api(
        self,
        course_id: str = None,
        ready_to_sync: bool = None,
        upstream_usage_key: str = None,
    ):
        data = {}
        if course_id is not None:
            data["course_id"] = str(course_id)
        if ready_to_sync is not None:
            data["ready_to_sync"] = str(ready_to_sync)
        if upstream_usage_key is not None:
            data["upstream_usage_key"] = str(upstream_usage_key)
        return self.client.get("/api/contentstore/v2/downstreams/", data=data)

    def test_200_all_downstreams_for_a_course(self):
        """
        Returns all links for given course
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(course_id=self.course.id)
        assert response.status_code == 200
        data = response.json()
        date_format = self.now.isoformat().split("+")[0] + 'Z'
        expected = [
            {
                'created': date_format,
                'downstream_context_key': str(self.course.id),
                'downstream_usage_key': str(self.downstream_video_key),
                'id': 1,
                'ready_to_sync': False,
                'updated': date_format,
                'upstream_context_key': self.library_id,
                'upstream_context_title': self.library_title,
                'upstream_usage_key': self.video_lib_id,
                'upstream_version': 1,
                'version_declined': None,
                'version_synced': 1
            },
            {
                'created': date_format,
                'downstream_context_key': str(self.course.id),
                'downstream_usage_key': str(self.downstream_html_key),
                'id': 2,
                'ready_to_sync': True,
                'updated': date_format,
                'upstream_context_key': self.library_id,
                'upstream_context_title': self.library_title,
                'upstream_usage_key': self.html_lib_id,
                'upstream_version': 2,
                'version_declined': None,
                'version_synced': 1,
            },
        ]
        self.assertListEqual(data["results"], expected)
        self.assertEqual(data["count"], 2)

    def test_200_all_downstreams_ready_to_sync(self):
        """
        Returns all links that are syncable
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(ready_to_sync=True)
        assert response.status_code == 200
        data = response.json()
        self.assertTrue(all(o["ready_to_sync"] for o in data["results"]))
        self.assertEqual(data["count"], 1)

    def test_200_downstream_context_list(self):
        """
        Returns all downstream courses for given library block
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(upstream_usage_key=self.video_lib_id)
        assert response.status_code == 200
        data = response.json()
        expected = [str(self.downstream_video_key)] + [str(key) for key in self.another_video_keys]
        got = [str(o["downstream_usage_key"]) for o in data["results"]]
        self.assertListEqual(got, expected)
        self.assertEqual(data["count"], 4)


class GetDownstreamSummaryViewTest(
    _BaseDownstreamViewTestMixin,
    SharedModuleStoreTestCase,
):
    """
    Test that `GET /api/v2/contentstore/downstreams/<course_id>/summary` returns summary of links in course.
    """
    def call_api(self, course_id):
        return self.client.get(f"/api/contentstore/v2/downstreams/{course_id}/summary")

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    def test_200_summary(self):
        """
        Does the happy path work?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(str(self.another_course.id))
        assert response.status_code == 200
        data = response.json()
        expected = [{
            'upstream_context_title': 'Test Library 1',
            'upstream_context_key': self.library_id,
            'ready_to_sync_count': 0,
            'total_count': 3,
            'last_published_at': self.now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }]
        self.assertListEqual(data, expected)
        response = self.call_api(str(self.course.id))
        assert response.status_code == 200
        data = response.json()
        expected = [{
            'upstream_context_title': 'Test Library 1',
            'upstream_context_key': self.library_id,
            'ready_to_sync_count': 1,
            'total_count': 2,
            'last_published_at': self.now.strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
        }]
        self.assertListEqual(data, expected)
