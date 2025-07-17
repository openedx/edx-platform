# pylint: disable=unused-import
"""
Tests the forum notification views.
"""

import json
import logging
from datetime import datetime
from unittest import mock
from unittest.mock import ANY, Mock, call, patch

import ddt
import pytest
from django.conf import settings
from django.http import Http404
from django.test.client import Client, RequestFactory
from django.test.utils import override_settings
from django.urls import reverse
from django.utils import translation
from edx_django_utils.cache import RequestCache
from edx_toggles.toggles.testutils import override_waffle_flag
from lms.djangoapps.discussion.django_comment_client.tests.mixins import (
    MockForumApiMixin,
)
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (
    TEST_DATA_SPLIT_MODULESTORE,
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
)
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    BlockFactory,
    check_mongo_calls,
)

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.roles import CourseStaffRole, UserBasedRole
from common.djangoapps.student.tests.factories import (
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)
from common.djangoapps.util.testing import EventTestMixin, UrlResetMixin
from lms.djangoapps.courseware.exceptions import CourseAccessRedirect
from lms.djangoapps.discussion import views
from lms.djangoapps.discussion.django_comment_client.constants import (
    TYPE_ENTRY,
    TYPE_SUBCATEGORY,
)
from lms.djangoapps.discussion.django_comment_client.permissions import get_team
from lms.djangoapps.discussion.django_comment_client.tests.group_id import (
    CohortedTopicGroupIdTestMixinV2,
    GroupIdAssertionMixinV2,
    NonCohortedTopicGroupIdTestMixinV2,
)
from lms.djangoapps.discussion.django_comment_client.tests.unicode import (
    UnicodeTestMixin,
)
from lms.djangoapps.discussion.django_comment_client.tests.utils import (
    CohortedTestCase,
    ForumsEnableMixin,
    config_course_discussions,
    topic_name_to_id,
)
from lms.djangoapps.discussion.django_comment_client.utils import strip_none
from lms.djangoapps.discussion.toggles import ENABLE_DISCUSSIONS_MFE
from lms.djangoapps.discussion.views import (
    _get_discussion_default_topic_id,
    course_discussions_settings_handler,
)
from lms.djangoapps.teams.tests.factories import (
    CourseTeamFactory,
    CourseTeamMembershipFactory,
)
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from openedx.core.djangoapps.course_groups.tests.helpers import config_course_cohorts
from openedx.core.djangoapps.course_groups.tests.test_views import CohortViewsTestCase
from openedx.core.djangoapps.django_comment_common.comment_client.utils import (
    CommentClientPaginatedResult,
)
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_STUDENT,
    CourseDiscussionSettings,
    ForumsConfig,
)
from openedx.core.djangoapps.django_comment_common.utils import (
    ThreadContext,
    seed_permissions_roles,
)
from openedx.core.djangoapps.util.testing import ContentGroupTestCase
from openedx.core.djangoapps.waffle_utils.testutils import WAFFLE_TABLES
from openedx.core.lib.teams_config import TeamsConfig
from openedx.features.content_type_gating.models import ContentTypeGatingConfig
from openedx.features.enterprise_support.tests.mixins.enterprise import (
    EnterpriseTestConsentRequired,
)

log = logging.getLogger(__name__)

QUERY_COUNT_TABLE_IGNORELIST = WAFFLE_TABLES


def make_mock_thread_data(
    course,
    text,
    thread_id,
    num_children,
    group_id=None,
    group_name=None,
    commentable_id=None,
    is_commentable_divided=None,
    anonymous=False,
    anonymous_to_peers=False,
):
    """
    Creates mock thread data for testing purposes.
    """
    data_commentable_id = (
        commentable_id
        or course.discussion_topics.get("General", {}).get("id")
        or "dummy_commentable_id"
    )
    thread_data = {
        "id": thread_id,
        "type": "thread",
        "title": text,
        "body": text,
        "commentable_id": data_commentable_id,
        "resp_total": 42,
        "resp_skip": 25,
        "resp_limit": 5,
        "group_id": group_id,
        "anonymous": anonymous,
        "anonymous_to_peers": anonymous_to_peers,
        "context": (
            ThreadContext.COURSE
            if get_team(data_commentable_id) is None
            else ThreadContext.STANDALONE
        ),
    }
    if group_id is not None:
        thread_data["group_name"] = group_name
    if is_commentable_divided is not None:
        thread_data["is_commentable_divided"] = is_commentable_divided
    if num_children is not None:
        thread_data["children"] = [
            {
                "id": f"dummy_comment_id_{i}",
                "type": "comment",
                "body": text,
            }
            for i in range(num_children)
        ]
    return thread_data


def make_mock_collection_data(
    course,
    text,
    thread_id,
    num_children=None,
    group_id=None,
    commentable_id=None,
    thread_list=None,
):
    """
    Creates mock collection data for testing purposes.
    """
    if thread_list:
        return [
            make_mock_thread_data(
                course=course, text=text, num_children=num_children, **thread
            )
            for thread in thread_list
        ]
    else:
        return [
            make_mock_thread_data(
                course=course,
                text=text,
                thread_id=thread_id,
                num_children=num_children,
                group_id=group_id,
                commentable_id=commentable_id,
            )
        ]


def make_collection_callback(
    course,
    text,
    thread_id="dummy_thread_id",
    group_id=None,
    commentable_id=None,
    thread_list=None,
):
    """
    Creates a callback function for simulating collection data.
    """

    def callback(*args, **kwargs):
        # Simulate default user thread response
        return {
            "collection": make_mock_collection_data(
                course, text, thread_id, None, group_id, commentable_id, thread_list
            )
        }

    return callback


def make_thread_callback(
    course,
    text,
    thread_id="dummy_thread_id",
    group_id=None,
    commentable_id=None,
    num_thread_responses=1,
    anonymous=False,
    anonymous_to_peers=False,
):
    """
    Creates a callback function for simulating thread data.
    """

    def callback(*args, **kwargs):
        # Simulate default user thread response
        return make_mock_thread_data(
            course=course,
            text=text,
            thread_id=thread_id,
            num_children=num_thread_responses,
            group_id=group_id,
            commentable_id=commentable_id,
            anonymous=anonymous,
            anonymous_to_peers=anonymous_to_peers,
        )

    return callback


def make_user_callback():
    """
    Creates a callback function for simulating user data.
    """

    def callback(*args, **kwargs):
        res = {
            "default_sort_key": "date",
            "upvoted_ids": [],
            "downvoted_ids": [],
            "subscribed_thread_ids": [],
        }
        # comments service adds these attributes when course_id param is present
        if kwargs.get("course_id"):
            res.update({"threads_count": 1, "comments_count": 2})
        return res

    return callback


class ForumViewsUtilsMixin(MockForumApiMixin):
    """
    Utils for the Forum Views.
    """

    def _configure_mock_responses(
        self,
        course,
        text,
        thread_id="dummy_thread_id",
        group_id=None,
        commentable_id=None,
        num_thread_responses=1,
        thread_list=None,
        anonymous=False,
        anonymous_to_peers=False,
    ):
        """
        Configure mock responses for the Forum Views.
        """
        for func_name in [
            "search_threads",
            "get_user_active_threads",
            "get_user_threads",
        ]:
            self.set_mock_side_effect(
                func_name,
                make_collection_callback(
                    course,
                    text,
                    thread_id,
                    group_id,
                    commentable_id,
                    thread_list,
                ),
            )

        self.set_mock_side_effect(
            "get_thread",
            make_thread_callback(
                course,
                text,
                thread_id,
                group_id,
                commentable_id,
                num_thread_responses,
                anonymous,
                anonymous_to_peers,
            ),
        )

        self.set_mock_side_effect("get_user", make_user_callback())


class ForumFormDiscussionContentGroupTestCase(
    ForumsEnableMixin, ContentGroupTestCase, ForumViewsUtilsMixin
):
    """
    Tests `forum_form_discussion api` works with different content groups.
    Discussion blocks are setup in ContentGroupTestCase class i.e
    alpha_block => alpha_group_discussion => alpha_cohort => alpha_user/community_ta
    beta_block => beta_group_discussion => beta_cohort => beta_user
    """

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()
        self.thread_list = [
            {"thread_id": "test_general_thread_id"},
            {
                "thread_id": "test_global_group_thread_id",
                "commentable_id": self.global_block.discussion_id,
            },
            {
                "thread_id": "test_alpha_group_thread_id",
                "group_id": self.alpha_block.group_access[0][0],
                "commentable_id": self.alpha_block.discussion_id,
            },
            {
                "thread_id": "test_beta_group_thread_id",
                "group_id": self.beta_block.group_access[0][0],
                "commentable_id": self.beta_block.discussion_id,
            },
        ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def assert_has_access(self, response, expected_discussion_threads):
        """
        Verify that a users have access to the threads in their assigned
        cohorts and non-cohorted blocks.
        """
        discussion_data = json.loads(response.content.decode("utf-8"))[
            "discussion_data"
        ]
        assert len(discussion_data) == expected_discussion_threads

    def call_view(
        self, user
    ):  # lint-amnesty, pylint: disable=missing-function-docstring
        self._configure_mock_responses(
            course=self.course, text="dummy content", thread_list=self.thread_list
        )
        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        return self.client.get(
            reverse("forum_form_discussion", args=[str(self.course.id)]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

    def test_community_ta_user(self):
        """
        Verify that community_ta user has access to all threads regardless
        of cohort.
        """
        response = self.call_view(self.community_ta)
        self.assert_has_access(response, 4)

    def test_alpha_cohort_user(self):
        """
        Verify that alpha_user has access to alpha_cohort and non-cohorted
        threads.
        """
        response = self.call_view(self.alpha_user)
        self.assert_has_access(response, 3)

    def test_beta_cohort_user(self):
        """
        Verify that beta_user has access to beta_cohort and non-cohorted
        threads.
        """
        response = self.call_view(self.beta_user)
        self.assert_has_access(response, 3)

    def test_global_staff_user(self):
        """
        Verify that global staff user has access to all threads regardless
        of cohort.
        """
        response = self.call_view(self.staff_user)
        self.assert_has_access(response, 4)


class ForumFormDiscussionUnicodeTestCase(
    ForumsEnableMixin,
    SharedModuleStoreTestCase,
    UnicodeTestMixin,
    ForumViewsUtilsMixin,
):
    """
    Discussiin Unicode Tests.
    """

    @classmethod
    def setUpClass(cls):  # pylint: disable=super-method-not-called
        super().setUpClassAndForumMock()

        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    def _test_unicode_data(
        self, text
    ):  # lint-amnesty, pylint: disable=missing-function-docstring
        self._configure_mock_responses(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        # so (request.headers.get('x-requested-with') == 'XMLHttpRequest') == True
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

        response = views.forum_form_discussion(request, str(self.course.id))
        assert response.status_code == 200
        response_data = json.loads(response.content.decode("utf-8"))
        assert response_data["discussion_data"][0]["title"] == text
        assert response_data["discussion_data"][0]["body"] == text


class EnterpriseConsentTestCase(
    EnterpriseTestConsentRequired,
    ForumsEnableMixin,
    UrlResetMixin,
    ModuleStoreTestCase,
    ForumViewsUtilsMixin,
):
    """
    Ensure that the Enterprise Data Consent redirects are in place only when consent is required.
    """

    CREATE_USER = False

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        # Invoke UrlResetMixin setUp
        super().setUp()
        username = "foo"
        password = "bar"

        self.discussion_id = "dummy_discussion_id"
        self.course = CourseFactory.create(
            discussion_topics={"dummy discussion": {"id": self.discussion_id}}
        )
        self.student = UserFactory.create(username=username, password=password)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        assert self.client.login(username=username, password=password)

        self.addCleanup(translation.deactivate)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    @patch("openedx.features.enterprise_support.api.enterprise_customer_for_request")
    def test_consent_required(self, mock_enterprise_customer_for_request):
        """
        Test that enterprise data sharing consent is required when enabled for the various discussion views.
        """
        # ENT-924: Temporary solution to replace sensitive SSO usernames.
        mock_enterprise_customer_for_request.return_value = None

        thread_id = "dummy"
        course_id = str(self.course.id)
        self._configure_mock_responses(
            course=self.course, text="dummy", thread_id=thread_id
        )

        for url in (
            reverse("forum_form_discussion", kwargs=dict(course_id=course_id)),
            reverse(
                "single_thread",
                kwargs=dict(
                    course_id=course_id,
                    discussion_id=self.discussion_id,
                    thread_id=thread_id,
                ),
            ),
        ):
            self.verify_consent_required(  # pylint: disable=no-value-for-parameter
                self.client, url
            )


class InlineDiscussionGroupIdTestCase(  # lint-amnesty, pylint: disable=missing-class-docstring
    CohortedTestCase,
    CohortedTopicGroupIdTestMixinV2,
    NonCohortedTopicGroupIdTestMixinV2,
    ForumViewsUtilsMixin,
):
    function_name = "get_user_threads"

    def setUp(self):
        super().setUp()
        self.cohorted_commentable_id = "cohorted_topic"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def call_view(
        self, commentable_id, user, group_id, pass_group_id=True
    ):  # pylint: disable=arguments-differ
        kwargs = {"commentable_id": self.cohorted_commentable_id}
        if group_id:
            # avoid causing a server error when the LMS chokes attempting
            # to find a group name for the group_id, when we're testing with
            # an invalid one.
            try:
                CourseUserGroup.objects.get(id=group_id)
                kwargs["group_id"] = group_id
            except CourseUserGroup.DoesNotExist:
                pass
        self._configure_mock_responses(self.course, "dummy content", **kwargs)

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        request = RequestFactory().get("dummy_url", data=request_data)
        request.user = user
        return views.inline_discussion(request, str(self.course.id), commentable_id)

    def test_group_info_in_ajax_response(self):
        response = self.call_view(
            self.cohorted_commentable_id, self.student, self.student_cohort.id
        )
        self._assert_json_response_contains_group_info(
            response, lambda d: d["discussion_data"][0]
        )


class InlineDiscussionContextTestCase(
    ForumsEnableMixin, ModuleStoreTestCase, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()
        CourseEnrollmentFactory(user=self.user, course_id=self.course.id)
        self.discussion_topic_id = "dummy_topic"
        self.team = CourseTeamFactory(
            name="A team",
            course_id=self.course.id,
            topic_id="topic_id",
            discussion_topic_id=self.discussion_topic_id,
        )

        self.team.add_user(self.user)
        self.user_not_in_team = UserFactory.create()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def test_context_can_be_standalone(self):
        self._configure_mock_responses(
            course=self.course,
            text="dummy text",
            commentable_id=self.discussion_topic_id,
        )

        request = RequestFactory().get("dummy_url")
        request.user = self.user

        response = views.inline_discussion(
            request,
            str(self.course.id),
            self.discussion_topic_id,
        )

        json_response = json.loads(response.content.decode("utf-8"))
        assert (
            json_response["discussion_data"][0]["context"] == ThreadContext.STANDALONE
        )

    def test_private_team_discussion(self):
        # First set the team discussion to be private
        CourseEnrollmentFactory(user=self.user_not_in_team, course_id=self.course.id)
        request = RequestFactory().get("dummy_url")
        request.user = self.user_not_in_team

        self._configure_mock_responses(
            course=self.course,
            text="dummy text",
            commentable_id=self.discussion_topic_id,
        )

        with patch(
            "lms.djangoapps.teams.api.is_team_discussion_private", autospec=True
        ) as mocked:
            mocked.return_value = True
            response = views.inline_discussion(
                request,
                str(self.course.id),
                self.discussion_topic_id,
            )
            assert response.status_code == 403
            assert response.content.decode("utf-8") == views.TEAM_PERMISSION_MESSAGE


class UserProfileDiscussionGroupIdTestCase(
    CohortedTestCase, CohortedTopicGroupIdTestMixinV2, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring
    function_name = "get_user_active_threads"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def call_view_for_profiled_user(
        self, requesting_user, profiled_user, group_id, pass_group_id, is_ajax=False
    ):
        """
        Calls "user_profile" view method on behalf of "requesting_user" to get information about
        the user "profiled_user".
        """
        kwargs = {}
        if group_id:
            kwargs["group_id"] = group_id
        self._configure_mock_responses(self.course, "dummy content", **kwargs)

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        headers = {}
        if is_ajax:
            headers["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

        self.client.login(
            username=requesting_user.username, password=self.TEST_PASSWORD
        )
        return self.client.get(
            reverse("user_profile", args=[str(self.course.id), profiled_user.id]),
            data=request_data,
            **headers,
        )

    def call_view(
        self, _commentable_id, user, group_id, pass_group_id=True, is_ajax=False
    ):  # pylint: disable=arguments-differ
        return self.call_view_for_profiled_user(
            user, user, group_id, pass_group_id=pass_group_id, is_ajax=is_ajax
        )

    def test_group_info_in_html_response(self):
        response = self.call_view(
            "cohorted_topic", self.student, self.student_cohort.id, is_ajax=False
        )
        self._assert_html_response_contains_group_info(response)

    def test_group_info_in_ajax_response(self):
        response = self.call_view(
            "cohorted_topic", self.student, self.student_cohort.id, is_ajax=True
        )
        self._assert_json_response_contains_group_info(
            response, lambda d: d["discussion_data"][0]
        )

    def _test_group_id_passed_to_user_profile(
        self,
        expect_group_id_in_request,
        requesting_user,
        profiled_user,
        group_id,
        pass_group_id,
    ):
        """
        Helper method for testing whether or not group_id was passed to the user_profile request.
        """

        def get_params_from_user_info_call(for_specific_course):
            """
            Returns the request parameters for the user info call with either course_id specified or not,
            depending on value of 'for_specific_course'.
            """
            # There will be 3 calls from user_profile. One has the cs_endpoint "active_threads", and it is already
            # tested. The other 2 calls are for user info; one of those calls is for general information about the user,
            # and it does not specify a course_id. The other call does specify a course_id, and if the caller did not
            # have discussion moderator privileges, it should also contain a group_id.
            user_func_calls = self.get_mock_func_calls("get_user")
            for r_call in user_func_calls:
                has_course_id = "course_id" in r_call[1]
                if (for_specific_course and has_course_id) or (
                    not for_specific_course and not has_course_id
                ):
                    return r_call[1]
            pytest.fail(
                f"Did not find appropriate user_profile call for 'for_specific_course'={for_specific_course}"
            )

        self.call_view_for_profiled_user(
            requesting_user,
            profiled_user,
            group_id,
            pass_group_id=pass_group_id,
            is_ajax=False,
        )
        # Should never have a group_id if course_id was not included in the request.
        params_without_course_id = get_params_from_user_info_call(False)
        assert "group_ids" not in params_without_course_id

        params_with_course_id = get_params_from_user_info_call(True)
        if expect_group_id_in_request:
            assert "group_ids" in params_with_course_id
            assert [group_id] == params_with_course_id["group_ids"]
        else:
            assert "group_ids" not in params_with_course_id

    def test_group_id_passed_to_user_profile_student(self):
        """
        Test that the group id is always included when requesting user profile information for a particular
        course if the requester does not have discussion moderation privileges.
        """

        def verify_group_id_always_present(profiled_user, pass_group_id):
            """
            Helper method to verify that group_id is always present for student in course
            (non-privileged user).
            """
            self._test_group_id_passed_to_user_profile(
                True, self.student, profiled_user, self.student_cohort.id, pass_group_id
            )

        # In all these test cases, the requesting_user is the student (non-privileged user).
        # The profile returned on behalf of the student is for the profiled_user.
        verify_group_id_always_present(profiled_user=self.student, pass_group_id=True)
        verify_group_id_always_present(profiled_user=self.student, pass_group_id=False)
        verify_group_id_always_present(profiled_user=self.moderator, pass_group_id=True)
        verify_group_id_always_present(
            profiled_user=self.moderator, pass_group_id=False
        )

    def test_group_id_user_profile_moderator(self):
        """
        Test that the group id is only included when a privileged user requests user profile information for a
        particular course and user if the group_id is explicitly passed in.
        """

        def verify_group_id_present(
            profiled_user, pass_group_id, requested_cohort=self.moderator_cohort
        ):
            """
            Helper method to verify that group_id is present.
            """
            self._test_group_id_passed_to_user_profile(
                True, self.moderator, profiled_user, requested_cohort.id, pass_group_id
            )

        def verify_group_id_not_present(
            profiled_user, pass_group_id, requested_cohort=self.moderator_cohort
        ):
            """
            Helper method to verify that group_id is not present.
            """
            self._test_group_id_passed_to_user_profile(
                False, self.moderator, profiled_user, requested_cohort.id, pass_group_id
            )

        # In all these test cases, the requesting_user is the moderator (privileged user).

        # If the group_id is explicitly passed, it will be present in the request.
        verify_group_id_present(profiled_user=self.student, pass_group_id=True)
        verify_group_id_present(profiled_user=self.moderator, pass_group_id=True)
        verify_group_id_present(
            profiled_user=self.student,
            pass_group_id=True,
            requested_cohort=self.student_cohort,
        )

        # If the group_id is not explicitly passed, it will not be present because the requesting_user
        # has discussion moderator privileges.
        verify_group_id_not_present(profiled_user=self.student, pass_group_id=False)
        verify_group_id_not_present(profiled_user=self.moderator, pass_group_id=False)


@ddt.ddt
class ForumDiscussionXSSTestCase(
    ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

        username = "foo"
        password = "bar"

        self.course = CourseFactory.create()
        self.student = UserFactory.create(username=username, password=password)
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        assert self.client.login(username=username, password=password)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    @ddt.data(
        '"><script>alert(1)</script>',
        "<script>alert(1)</script>",
        "</script><script>alert(1)</script>",
    )
    @patch("common.djangoapps.student.models.user.cc.User.from_django_user")
    def test_forum_discussion_xss_prevent(self, malicious_code, mock_user):
        """
        Test that XSS attack is prevented
        """
        self.set_mock_return_value("get_user", {})
        self.set_mock_return_value("get_user_threads", {})
        self.set_mock_return_value("get_user_active_threads", {})
        mock_user.return_value.to_dict.return_value = {}
        reverse_url = "{}{}".format(
            reverse("forum_form_discussion", kwargs={"course_id": str(self.course.id)}),
            "/forum_form_discussion",
        )
        # Test that malicious code does not appear in html
        url = "{}?{}={}".format(reverse_url, "sort_key", malicious_code)
        resp = self.client.get(url)
        self.assertNotContains(resp, malicious_code)

    @ddt.data(
        '"><script>alert(1)</script>',
        "<script>alert(1)</script>",
        "</script><script>alert(1)</script>",
    )
    @patch("common.djangoapps.student.models.user.cc.User.from_django_user")
    @patch("common.djangoapps.student.models.user.cc.User.active_threads")
    def test_forum_user_profile_xss_prevent(
        self, malicious_code, mock_threads, mock_from_django_user
    ):
        """
        Test that XSS attack is prevented
        """
        mock_threads.return_value = [], 1, 1
        mock_from_django_user.return_value.to_dict.return_value = {
            "upvoted_ids": [],
            "downvoted_ids": [],
            "subscribed_thread_ids": [],
        }
        self._configure_mock_responses(course=self.course, text="dummy")

        url = reverse(
            "user_profile",
            kwargs={"course_id": str(self.course.id), "user_id": str(self.student.id)},
        )
        # Test that malicious code does not appear in html
        url_string = "{}?{}={}".format(url, "page", malicious_code)
        resp = self.client.get(url_string)
        self.assertNotContains(resp, malicious_code)


class InlineDiscussionTestCase(
    ForumsEnableMixin, ModuleStoreTestCase, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()

        self.course = CourseFactory.create(
            org="TestX",
            number="101",
            display_name="Test Course",
            teams_configuration=TeamsConfig(
                {
                    "topics": [
                        {
                            "id": "topic_id",
                            "name": "A topic",
                            "description": "A topic",
                        }
                    ]
                }
            ),
        )
        self.student = UserFactory.create()
        CourseEnrollmentFactory(user=self.student, course_id=self.course.id)
        self.discussion1 = BlockFactory.create(
            parent_location=self.course.location,
            category="discussion",
            discussion_id="discussion1",
            display_name="Discussion1",
            discussion_category="Chapter",
            discussion_target="Discussion1",
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def send_request(self, params=None):
        """
        Creates and returns a request with params set, and configures
        mock_request to return appropriate values.
        """
        request = RequestFactory().get("dummy_url", params if params else {})
        request.user = self.student
        self._configure_mock_responses(
            course=self.course,
            text="dummy content",
            commentable_id=self.discussion1.discussion_id,
        )
        return views.inline_discussion(
            request, str(self.course.id), self.discussion1.discussion_id
        )

    def test_context(self):
        team = CourseTeamFactory(
            name="Team Name",
            topic_id="topic_id",
            course_id=self.course.id,
            discussion_topic_id=self.discussion1.discussion_id,
        )

        team.add_user(self.student)

        self.send_request()
        last_call = self.get_mock_func_calls("get_user_threads")[-1][1]
        assert last_call["context"] == ThreadContext.STANDALONE


class ForumDiscussionSearchUnicodeTestCase(
    ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):  # pylint: disable=super-method-not-called
        super().setUpClassAndForumMock()
        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    def _test_unicode_data(
        self, text
    ):  # lint-amnesty, pylint: disable=missing-function-docstring
        self._configure_mock_responses(course=self.course, text=text)
        data = {
            "ajax": 1,
            "text": text,
        }
        request = RequestFactory().get("dummy_url", data)
        request.user = self.student
        # so (request.headers.get('x-requested-with') == 'XMLHttpRequest') == True
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

        response = views.forum_form_discussion(request, str(self.course.id))
        assert response.status_code == 200
        response_data = json.loads(response.content.decode("utf-8"))
        assert response_data["discussion_data"][0]["title"] == text
        assert response_data["discussion_data"][0]["body"] == text


class InlineDiscussionUnicodeTestCase(
    ForumsEnableMixin, SharedModuleStoreTestCase, UnicodeTestMixin, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring

    @classmethod
    def setUpClass(cls):  # pylint: disable=super-method-not-called
        super().setUpClassAndForumMock()

        with super().setUpClassAndTestData():
            cls.course = CourseFactory.create()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.student = UserFactory.create()
        CourseEnrollmentFactory(user=cls.student, course_id=cls.course.id)

    def _test_unicode_data(
        self, text
    ):  # lint-amnesty, pylint: disable=missing-function-docstring
        self._configure_mock_responses(course=self.course, text=text)
        request = RequestFactory().get("dummy_url")
        request.user = self.student

        response = views.inline_discussion(
            request, str(self.course.id), self.course.discussion_topics["General"]["id"]
        )
        assert response.status_code == 200
        response_data = json.loads(response.content.decode("utf-8"))
        assert response_data["discussion_data"][0]["title"] == text
        assert response_data["discussion_data"][0]["body"] == text


class ForumFormDiscussionGroupIdTestCase(
    CohortedTestCase, CohortedTopicGroupIdTestMixinV2, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring
    function_name = "get_user_threads"

    def call_view(
        self, commentable_id, user, group_id, pass_group_id=True, is_ajax=False
    ):  # pylint: disable=arguments-differ
        kwargs = {}
        if group_id:
            kwargs["group_id"] = group_id
        self._configure_mock_responses(self.course, "dummy content", **kwargs)

        request_data = {}
        if pass_group_id:
            request_data["group_id"] = group_id
        headers = {}
        if is_ajax:
            headers["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"

        self.client.login(username=user.username, password=self.TEST_PASSWORD)
        return self.client.get(
            reverse("forum_form_discussion", args=[str(self.course.id)]),
            data=request_data,
            **headers,
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def test_group_info_in_html_response(self):
        response = self.call_view(
            "cohorted_topic", self.student, self.student_cohort.id
        )
        self._assert_html_response_contains_group_info(response)

    def test_group_info_in_ajax_response(self):
        response = self.call_view(
            "cohorted_topic", self.student, self.student_cohort.id, is_ajax=True
        )
        self._assert_json_response_contains_group_info(
            response, lambda d: d["discussion_data"][0]
        )


class UserProfileTestCase(
    ForumsEnableMixin, UrlResetMixin, ModuleStoreTestCase, ForumViewsUtilsMixin
):  # lint-amnesty, pylint: disable=missing-class-docstring

    TEST_THREAD_TEXT = "userprofile-test-text"
    TEST_THREAD_ID = "userprofile-test-thread-id"

    @patch.dict("django.conf.settings.FEATURES", {"ENABLE_DISCUSSION_SERVICE": True})
    def setUp(self):
        super().setUp()

        self.course = CourseFactory.create()
        self.student = UserFactory.create()
        self.profiled_user = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)
        CourseEnrollmentFactory.create(
            user=self.profiled_user, course_id=self.course.id
        )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        super().setUpClassAndForumMock()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        super().disposeForumMocks()

    def get_response(
        self, params, **headers
    ):  # lint-amnesty, pylint: disable=missing-function-docstring
        self._configure_mock_responses(
            course=self.course,
            text=self.TEST_THREAD_TEXT,
            thread_id=self.TEST_THREAD_ID,
        )
        self.client.login(username=self.student.username, password=self.TEST_PASSWORD)

        response = self.client.get(
            reverse(
                "user_profile",
                kwargs={
                    "course_id": str(self.course.id),
                    "user_id": self.profiled_user.id,
                },
            ),
            data=params,
            **headers,
        )
        params = {
            "course_id": str(self.course.id),
            "page": params.get("page", 1),
            "per_page": views.THREADS_PER_PAGE,
        }
        self.check_mock_called_with("get_user_active_threads", -1, **params)
        return response

    def check_html(
        self, **params
    ):  # lint-amnesty, pylint: disable=missing-function-docstring
        response = self.get_response(params)
        assert response.status_code == 200
        assert response["Content-Type"] == "text/html; charset=utf-8"
        html = response.content.decode("utf-8")
        self.assertRegex(html, r'data-page="1"')
        self.assertRegex(html, r'data-num-pages="1"')
        self.assertRegex(
            html, r'<span class="discussion-count">1</span> discussion started'
        )
        self.assertRegex(html, r'<span class="discussion-count">2</span> comments')
        self.assertRegex(html, f"&#39;id&#39;: &#39;{self.TEST_THREAD_ID}&#39;")
        self.assertRegex(html, f"&#39;title&#39;: &#39;{self.TEST_THREAD_TEXT}&#39;")
        self.assertRegex(html, f"&#39;body&#39;: &#39;{self.TEST_THREAD_TEXT}&#39;")
        self.assertRegex(html, f"&#39;username&#39;: &#39;{self.student.username}&#39;")

    def check_ajax(
        self, **params
    ):  # lint-amnesty, pylint: disable=missing-function-docstring
        response = self.get_response(params, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/json; charset=utf-8"
        response_data = json.loads(response.content.decode("utf-8"))
        assert sorted(response_data.keys()) == [
            "annotated_content_info",
            "discussion_data",
            "num_pages",
            "page",
        ]
        assert len(response_data["discussion_data"]) == 1
        assert response_data["page"] == 1
        assert response_data["num_pages"] == 1
        assert response_data["discussion_data"][0]["id"] == self.TEST_THREAD_ID
        assert response_data["discussion_data"][0]["title"] == self.TEST_THREAD_TEXT
        assert response_data["discussion_data"][0]["body"] == self.TEST_THREAD_TEXT

    def test_html(self):
        self.check_html()

    def test_ajax(self):
        self.check_ajax()

    def test_404_non_enrolled_user(self):
        """
        Test that when student try to visit un-enrolled students' discussion profile,
        the system raises Http404.
        """
        unenrolled_user = UserFactory.create()
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with pytest.raises(Http404):
            views.user_profile(request, str(self.course.id), unenrolled_user.id)

    def test_404_profiled_user(self):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with pytest.raises(Http404):
            views.user_profile(request, str(self.course.id), -999)

    def test_404_course(self):
        request = RequestFactory().get("dummy_url")
        request.user = self.student
        with pytest.raises(Http404):
            views.user_profile(request, "non/existent/course", self.profiled_user.id)

    def test_post(self):
        self._configure_mock_responses(
            course=self.course,
            text=self.TEST_THREAD_TEXT,
            thread_id=self.TEST_THREAD_ID,
        )
        request = RequestFactory().post("dummy_url")
        request.user = self.student
        response = views.user_profile(
            request, str(self.course.id), self.profiled_user.id
        )
        assert response.status_code == 405
