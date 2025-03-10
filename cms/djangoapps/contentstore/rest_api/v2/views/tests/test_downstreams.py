"""
Unit tests for /api/contentstore/v2/downstreams/* JSON APIs.
"""
from datetime import datetime, timezone
from unittest.mock import patch

from django.conf import settings
from freezegun import freeze_time

from cms.djangoapps.contentstore.helpers import StaticFileNotices
from cms.lib.xblock.upstream_sync import BadUpstream, UpstreamLink
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import BlockFactory, CourseFactory

from .. import downstreams as downstreams_views

MOCK_LIB_KEY = "lib:OpenedX:CSPROB3"
MOCK_UPSTREAM_REF = "lb:OpenedX:CSPROB3:video:843b4c73-1e2d-4ced-a0ff-24e503cdb3e4"
MOCK_HTML_UPSTREAM_REF = "lb:OpenedX:CSPROB3:html:843b4c73-1e2d-4ced-a0ff-24e503cdb3e4"
MOCK_UPSTREAM_LINK = "{mfe_url}/library/{lib_key}/components?usageKey={usage_key}".format(
    mfe_url=settings.COURSE_AUTHORING_MICROFRONTEND_URL,
    lib_key=MOCK_LIB_KEY,
    usage_key=MOCK_UPSTREAM_REF,
)
MOCK_UPSTREAM_ERROR = "your LibraryGPT subscription has expired"


def _get_upstream_link_good_and_syncable(downstream):
    return UpstreamLink(
        upstream_ref=downstream.upstream,
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
        self.course = CourseFactory.create()
        chapter = BlockFactory.create(category='chapter', parent=self.course)
        sequential = BlockFactory.create(category='sequential', parent=chapter)
        unit = BlockFactory.create(category='vertical', parent=sequential)
        self.regular_video_key = BlockFactory.create(category='video', parent=unit).usage_key
        self.downstream_video_key = BlockFactory.create(
            category='video', parent=unit, upstream=MOCK_UPSTREAM_REF, upstream_version=123,
        ).usage_key
        self.downstream_html_key = BlockFactory.create(
            category='html', parent=unit, upstream=MOCK_HTML_UPSTREAM_REF, upstream_version=1,
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
                    category="video", parent=another_unit, upstream=MOCK_UPSTREAM_REF, upstream_version=123,
                ).usage_key
            )

        self.fake_video_key = self.course.id.make_usage_key("video", "NoSuchVideo")
        self.superuser = UserFactory(username="superuser", password="password", is_staff=True, is_superuser=True)
        self.learner = UserFactory(username="learner", password="password")

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
        assert response.data['upstream_ref'] == MOCK_UPSTREAM_REF
        assert response.data['error_message'] is None
        assert response.data['ready_to_sync'] is True
        assert response.data['upstream_link'] == MOCK_UPSTREAM_LINK

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_bad)
    def test_200_bad_upstream(self):
        """
        If the upstream link is broken, do we still return 200, but with an error message in body?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 200
        assert response.data['upstream_ref'] == MOCK_UPSTREAM_REF
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
            data={
                "upstream_ref": MOCK_UPSTREAM_REF,
                **({"sync": sync} if sync else {}),
            },
            content_type="application/json",
        )

    @patch.object(downstreams_views, "fetch_customizable_fields")
    @patch.object(downstreams_views, "sync_from_upstream")
    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    def test_200_with_sync(self, mock_sync, mock_fetch):
        """
        Does the happy path work (with sync=True)?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.regular_video_key, sync='true')
        assert response.status_code == 200
        video_after = modulestore().get_item(self.regular_video_key)
        assert mock_sync.call_count == 1
        assert mock_fetch.call_count == 0
        assert video_after.upstream == MOCK_UPSTREAM_REF

    @patch.object(downstreams_views, "fetch_customizable_fields")
    @patch.object(downstreams_views, "sync_from_upstream")
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
        assert video_after.upstream == MOCK_UPSTREAM_REF

    @patch.object(downstreams_views, "fetch_customizable_fields", side_effect=BadUpstream(MOCK_UPSTREAM_ERROR))
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


class PostDownstreamSyncViewTest(_DownstreamSyncViewTestMixin, SharedModuleStoreTestCase):
    """
    Test that `POST /api/v2/contentstore/downstreams/.../sync` initiates a sync from the linked upstream.
    """
    def call_api(self, usage_key_string):
        return self.client.post(f"/api/contentstore/v2/downstreams/{usage_key_string}/sync")

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    @patch.object(downstreams_views, "sync_from_upstream")
    @patch.object(downstreams_views, "import_static_assets_for_library_sync", return_value=StaticFileNotices())
    @patch.object(downstreams_views, "clear_transcripts")
    def test_200(self, mock_sync_from_upstream, mock_import_staged_content, mock_clear_transcripts):
        """
        Does the happy path work?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 200
        assert mock_sync_from_upstream.call_count == 1
        assert mock_import_staged_content.call_count == 1
        assert mock_clear_transcripts.call_count == 1


class DeleteDownstreamSyncViewtest(_DownstreamSyncViewTestMixin, SharedModuleStoreTestCase):
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


class GetUpstreamViewTest(_BaseDownstreamViewTestMixin, SharedModuleStoreTestCase):
    """
    Test that `GET /api/v2/contentstore/upstreams/...` returns list of links in given downstream context i.e. course.
    """
    def call_api(self, usage_key_string):
        return self.client.get(f"/api/contentstore/v2/upstreams/{usage_key_string}")

    def test_200_all_upstreams(self):
        """
        Returns all upstream links for given course
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.course.id)
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
                'upstream_context_key': MOCK_LIB_KEY,
                'upstream_usage_key': MOCK_UPSTREAM_REF,
                'upstream_version': None,
                'version_declined': None,
                'version_synced': 123
            },
            {
                'created': date_format,
                'downstream_context_key': str(self.course.id),
                'downstream_usage_key': str(self.downstream_html_key),
                'id': 2,
                'ready_to_sync': False,
                'updated': date_format,
                'upstream_context_key': MOCK_LIB_KEY,
                'upstream_usage_key': MOCK_HTML_UPSTREAM_REF,
                'upstream_version': None,
                'version_declined': None,
                'version_synced': 1,
            },
        ]
        self.assertListEqual(data, expected)


class GetDownstreamContextsTest(_BaseDownstreamViewTestMixin, SharedModuleStoreTestCase):
    """
    Test that `GET /api/v2/contentstore/upstream/:usage_key/downstream-links returns list of
    linked blocks usage_keys in given upstream entity (i.e. library block).
    """
    def call_api(self, usage_key_string):
        return self.client.get(f"/api/contentstore/v2/upstream/{usage_key_string}/downstream-links")

    def test_200_downstream_context_list(self):
        """
        Returns all downstream courses for given library block
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(MOCK_UPSTREAM_REF)
        assert response.status_code == 200
        data = response.json()
        expected = [str(self.downstream_video_key)] + [str(key) for key in self.another_video_keys]
        self.assertListEqual(data, expected)
