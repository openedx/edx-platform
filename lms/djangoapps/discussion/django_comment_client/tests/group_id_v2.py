# pylint: disable=missing-docstring


import json
import re

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from lms.djangoapps.teams.tests.factories import CourseTeamFactory
from openedx.core.djangoapps.django_comment_common.models import (
    CourseDiscussionSettings,
)


from unittest.mock import patch


class GroupIdAssertionMixin:
    def _assert_forum_api_called_with_group_id(self, mock_function, group_id=None):
        assert mock_function.called
        assert mock_function.call_args[0][8] == group_id

    def _assert_forum_api_called_without_group_id(self, mock_function):
        assert mock_function.called
        assert mock_function.call_args[0][8] is None

    def _assert_html_response_contains_group_info(self, response):
        group_info = {"group_id": None, "group_name": None}
        match = re.search(r'"group_id": (\d*),', response.content.decode("utf-8"))
        if match and match.group(1) != "":
            group_info["group_id"] = int(match.group(1))
        match = re.search(r'"group_name": "(\w*)"', response.content.decode("utf-8"))
        if match:
            group_info["group_name"] = match.group(1)
        self._assert_thread_contains_group_info(group_info)

    def _assert_json_response_contains_group_info(self, response, extract_thread=None):
        payload = json.loads(response.content.decode("utf-8"))
        thread = extract_thread(payload) if extract_thread else payload
        self._assert_thread_contains_group_info(thread)

    def _assert_thread_contains_group_info(self, thread):
        assert thread["group_id"] == self.student_cohort.id
        assert thread["group_name"] == self.student_cohort.name


class CohortedTopicGroupIdTestMixin(GroupIdAssertionMixin):
    def call_view(
        self,
        mock_create_thread,
        mock_is_forum_v2_enabled,
        commentable_id,
        user,
        group_id,
        pass_group_id=True,
    ):
        pass

    def test_cohorted_topic_student_without_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.student,
            "",
            pass_group_id=False,
        )
        self._assert_forum_api_called_with_group_id(
            mock_create_thread, self.student_cohort.id
        )

    def test_cohorted_topic_student_none_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.student,
            "",
        )
        self._assert_forum_api_called_with_group_id(
            mock_create_thread, self.student_cohort.id
        )

    def test_cohorted_topic_student_with_own_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.student,
            self.student_cohort.id,
        )
        self._assert_forum_api_called_with_group_id(
            mock_create_thread, self.student_cohort.id
        )

    def test_cohorted_topic_student_with_other_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.student,
            self.moderator_cohort.id,
        )
        self._assert_forum_api_called_with_group_id(
            mock_create_thread, self.student_cohort.id
        )

    def test_cohorted_topic_moderator_without_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.moderator,
            "",
            pass_group_id=False,
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_cohorted_topic_moderator_none_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.moderator,
            "",
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_cohorted_topic_moderator_with_own_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.moderator,
            self.moderator_cohort.id,
        )
        self._assert_forum_api_called_with_group_id(
            mock_create_thread, self.moderator_cohort.id
        )

    def test_cohorted_topic_moderator_with_other_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.moderator,
            self.student_cohort.id,
        )
        self._assert_forum_api_called_with_group_id(
            mock_create_thread, self.student_cohort.id
        )

    def test_cohorted_topic_moderator_with_invalid_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        invalid_id = self.student_cohort.id + self.moderator_cohort.id
        response = self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.moderator,
            invalid_id,
        )
        assert response.status_code == 500

    def test_cohorted_topic_enrollment_track_invalid_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        CourseModeFactory.create(course_id=self.course.id, mode_slug=CourseMode.AUDIT)
        CourseModeFactory.create(
            course_id=self.course.id, mode_slug=CourseMode.VERIFIED
        )
        discussion_settings = CourseDiscussionSettings.get(self.course.id)
        discussion_settings.update(
            {
                "divided_discussions": ["cohorted_topic"],
                "division_scheme": CourseDiscussionSettings.ENROLLMENT_TRACK,
                "always_divide_inline_discussions": True,
            }
        )

        invalid_id = -1000
        response = self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "cohorted_topic",
            self.moderator,
            invalid_id,
        )
        assert response.status_code == 500


class NonCohortedTopicGroupIdTestMixin(GroupIdAssertionMixin):
    def call_view(
        self,
        mock_create_thread,
        mock_is_forum_v2_enabled,
        commentable_id,
        user,
        group_id,
        pass_group_id=True,
    ):
        pass

    def test_non_cohorted_topic_student_without_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.student,
            "",
            pass_group_id=False,
        )
        self._assert_forum_api_called_with_group_id(mock_create_thread)

    def test_non_cohorted_topic_student_none_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.student,
            "",
        )
        self._assert_forum_api_called_with_group_id(mock_create_thread)

    def test_non_cohorted_topic_student_with_own_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.student,
            self.student_cohort.id
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_non_cohorted_topic_student_with_other_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.student,
            self.moderator_cohort.id
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_non_cohorted_topic_moderator_without_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.moderator,
            "",
            pass_group_id=False,
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_non_cohorted_topic_moderator_none_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.moderator,
            ""
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_non_cohorted_topic_moderator_with_own_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.moderator,
            self.moderator_cohort.id,
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_non_cohorted_topic_moderator_with_other_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.moderator,
            self.student_cohort.id,
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_non_cohorted_topic_moderator_with_invalid_group_id(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        invalid_id = self.student_cohort.id + self.moderator_cohort.id
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            "non_cohorted_topic",
            self.moderator,
            invalid_id
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)

    def test_team_discussion_id_not_cohorted(
        self, mock_create_thread, mock_is_forum_v2_enabled
    ):
        team = CourseTeamFactory(course_id=self.course.id, topic_id="topic-id")

        team.add_user(self.student)
        self.call_view(
            mock_create_thread,
            mock_is_forum_v2_enabled,
            team.discussion_topic_id,
            self.student,
            "",
        )
        self._assert_forum_api_called_without_group_id(mock_create_thread)
