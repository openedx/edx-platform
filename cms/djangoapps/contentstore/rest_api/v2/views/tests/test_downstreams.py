"""
Unit tests for /api/contentstore/v2/downstreams/* JSON APIs.
"""
from unittest.mock import patch

from cms.lib.xblock.upstream_sync import UpstreamLink, BadUpstream
from common.djangoapps.student.tests.factories import UserFactory, CourseAccessRoleFactory
from common.djangoapps.student.roles import CourseStaffRole
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, BlockFactory

from .. import downstreams as downstreams_views


MOCK_UPSTREAM_REF = "mock-upstream-ref"
MOCK_UPSTREAM_ERROR = "your LibraryGPT subscription has expired"


def _get_upstream_link_good_and_syncable(downstream):
    return UpstreamLink(
        upstream_ref=downstream.upstream,
        version_synced=downstream.upstream_version,
        version_available=downstream.upstream_version + 1,
        version_declined=downstream.upstream_version_declined,
        error_message=None,
    )


def _get_upstream_link_bad(_downstream):
    raise BadUpstream(MOCK_UPSTREAM_ERROR)


class _DownstreamViewTestMixin:
    """
    Shared data and error test cases.
    """

    def setUp(self):
        """
        Create a simple course with one unit and two videos, one of which is linked to an "upstream".
        """
        super().setUp()
        self.course = CourseFactory.create()
        chapter = BlockFactory.create(category='chapter', parent=self.course)
        sequential = BlockFactory.create(category='sequential', parent=chapter)
        unit = BlockFactory.create(category='vertical', parent=sequential)
        self.regular_video_key = BlockFactory.create(category='video', parent=unit).usage_key
        self.downstream_video_key = BlockFactory.create(
            category='video', parent=unit, upstream=MOCK_UPSTREAM_REF, upstream_version=123,
        ).usage_key
        self.fake_video_key = self.course.id.make_usage_key("video", "NoSuchVideo")
        self.superuser = UserFactory(username="superuser", password="password", is_staff=True, is_superuser=True)
        self.learner = UserFactory(username="learner", password="password")

    def call_api(self, usage_key_string):
        raise NotImplementedError

    def test_400_no_upstream(self):
        """
        If the upstream link is missing, do we get a 400?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.regular_video_key)
        assert response.status_code == 400
        assert "is not linked" in response.data["developer_message"][0]

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


class _DownstreamWriteViewTestMixin(_DownstreamViewTestMixin):
    """
    Further shared data & tests for API views that WRITE to the downstream block.
    """
    def setUp(self):
        super().setUp()
        self.ta = UserFactory(username="teaching-assistant", password="password")
        CourseAccessRoleFactory.create(user=self.ta, course_id=self.course.id, role=CourseStaffRole.ROLE)

    def test_403_downstream_not_editable(self):
        """
        Do we raise 403 if the user has read access but lacks *write* access on the specified downstream block?
        """
        self.client.login(username="teaching-assistant", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 403
        assert "lacks permission to modify" in response.data["developer_message"]


class InspectDownstreamViewTest(_DownstreamViewTestMixin, SharedModuleStoreTestCase):
    """
    Tests for GET /api/v2/contentstore/downstreams/...
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


class CreateOrUpdateDownstreamViewTest(_DownstreamWriteViewTestMixin, SharedModuleStoreTestCase):
    """
    Tests for PUT /api/v2/contentstore/downstreams/...
    """
    def call_api(self, usage_key_string):
        return self.client.put(
            f"/api/contentstore/v2/downstreams/{usage_key_string}",
            data={
                "upstream_ref": "TODO",
                "sync": False,
            },
        )

    def test_200(self):
        """
        Does the happy path work?
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 200
        # @@TODO more assertions


class AcceptSyncFromUpstreamViewTest(_DownstreamWriteViewTestMixin, SharedModuleStoreTestCase):
    """
    Tests for POST /api/v2/contentstore/downstreams/.../sync
    """
    def call_api(self, usage_key_string):
        return self.client.post(f"/api/contentstore/v2/downstreams/{usage_key_string}/sync")

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    @patch.object(downstreams_views, "sync_from_upstream")
    def test_200(self, mock_sync_from_upstream):
        """
        @@TODO
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 200
        assert mock_sync_from_upstream.call_count == 1


class DeclineSyncFromUpstreamViewTest(_DownstreamWriteViewTestMixin, SharedModuleStoreTestCase):
    """
    Tests for DELETE /api/v2/contentstore/downstreams/.../sync
    """
    def call_api(self, usage_key_string):
        return self.client.delete(f"/api/contentstore/v2/downstreams/{usage_key_string}/sync")

    @patch.object(UpstreamLink, "get_for_block", _get_upstream_link_good_and_syncable)
    @patch.object(downstreams_views, "decline_sync")
    def test_200(self, mock_decline_sync):
        """
        @@TODO
        """
        self.client.login(username="superuser", password="password")
        response = self.call_api(self.downstream_video_key)
        assert response.status_code == 204
        assert mock_decline_sync.call_count == 1
