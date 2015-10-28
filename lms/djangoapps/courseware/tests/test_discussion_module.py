# -*- coding: utf-8 -*-
"""Test for Discussion Xmodule functional logic."""
from mock import Mock
from . import BaseTestXmodule
from courseware.module_render import get_module_for_descriptor_internal


class DiscussionModuleTest(BaseTestXmodule):
    """Logic tests for Discussion Xmodule."""
    CATEGORY = "discussion"

    def test_html_with_user(self):
        discussion = get_module_for_descriptor_internal(
            user=self.users[0],
            descriptor=self.item_descriptor,
            student_data=Mock(name='student_data'),
            course_id=self.course.id,
            track_function=Mock(name='track_function'),
            xqueue_callback_url_prefix=Mock(name='xqueue_callback_url_prefix'),
            request_token='request_token',
        )

        fragment = discussion.render('student_view')
        html = fragment.content
        self.assertIn('data-user-create-comment="false"', html)
        self.assertIn('data-user-create-subcomment="false"', html)
