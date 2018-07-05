"""
Tests for vertical module.
"""

# pylint: disable=protected-access
from __future__ import absolute_import, division, print_function, unicode_literals

from collections import namedtuple
import json

import ddt
from fs.memoryfs import MemoryFS
from mock import Mock, patch

from . import get_test_system
from .helpers import StubUserService
from .xml import XModuleXmlImportTest
from .xml import factories as xml
from ..x_module import STUDENT_VIEW, AUTHOR_VIEW, PUBLIC_VIEW

COMPLETION_DELAY = 9876

JsonRequest = namedtuple('JsonRequest', ['method', 'body'])


def get_json_request(data):
    """
    Given a data dictionary, return an appropriate JSON request.
    """
    return JsonRequest(
        method='POST',
        body=json.dumps(data),
    )


class StubCompletionService(object):
    """
    A stub implementation of the CompletionService for testing without access to django
    """

    def __init__(self, enabled, completion_value):
        self._enabled = enabled
        self._completion_value = completion_value
        self.delay = COMPLETION_DELAY

    def completion_tracking_enabled(self):
        """
        Turn on or off completion tracking for clients of the
        StubCompletionService.
        """
        return self._enabled

    def get_completions(self, candidates):
        """
        Return the (dummy) completion values for each specified candidate
        block.
        """
        return {candidate: self._completion_value for candidate in candidates}

    def get_complete_on_view_delay_ms(self):
        """
        Return the completion-by-viewing delay in milliseconds.
        """
        return self.delay

    def blocks_to_mark_complete_on_view(self, blocks):
        return {} if self._completion_value == 1.0 else blocks


class BaseVerticalBlockTest(XModuleXmlImportTest):
    """
    Tests for the BaseVerticalBlock.
    """
    test_html_1 = 'Test HTML 1'
    test_html_2 = 'Test HTML 2'

    def setUp(self):
        super(BaseVerticalBlockTest, self).setUp()
        # construct module
        course = xml.CourseFactory.build()
        sequence = xml.SequenceFactory.build(parent=course)
        vertical = xml.VerticalFactory.build(parent=sequence)

        self.course = self.process_xml(course)
        xml.HtmlFactory(parent=vertical, url_name='test-html-1', text=self.test_html_1)
        xml.HtmlFactory(parent=vertical, url_name='test-html-2', text=self.test_html_2)

        self.course = self.process_xml(course)
        course_seq = self.course.get_children()[0]
        self.module_system = get_test_system()

        self.module_system.descriptor_runtime = self.course._runtime
        self.course.runtime.export_fs = MemoryFS()

        self.vertical = course_seq.get_children()[0]
        self.vertical.xmodule_runtime = self.module_system

        self.html1block = self.vertical.get_children()[0]
        self.html2block = self.vertical.get_children()[1]

        self.username = "bilbo"
        self.default_context = {"bookmarked": False, "username": self.username}


@ddt.ddt
class VerticalBlockTestCase(BaseVerticalBlockTest):
    """
    Tests for the VerticalBlock.
    """
    shard = 1

    def assert_bookmark_info(self, assertion, content):
        """
        Assert content has/hasn't all the bookmark info.
        """
        assertion('bookmark_id', content)
        assertion('{},{}'.format(self.username, unicode(self.vertical.location)), content)
        assertion('bookmarked', content)
        assertion('show_bookmark_button', content)

    @ddt.unpack
    @ddt.data(
        {'context': None, 'view': STUDENT_VIEW},
        {'context': {}, 'view': STUDENT_VIEW},
        {'context': {}, 'view': PUBLIC_VIEW},
    )
    def test_render_student_preview_view(self, context, view):
        """
        Test the rendering of the student and public view.
        """
        self.module_system._services['bookmarks'] = Mock()
        if view == STUDENT_VIEW:
            self.module_system._services['user'] = StubUserService()
            self.module_system._services['completion'] = StubCompletionService(enabled=True, completion_value=0.0)
        elif view == PUBLIC_VIEW:
            self.module_system._services['user'] = StubUserService(is_anonymous=True)

        html = self.module_system.render(
            self.vertical, view, self.default_context if context is None else context
        ).content
        self.assertIn(self.test_html_1, html)
        self.assertIn(self.test_html_2, html)
        if view == STUDENT_VIEW:
            self.assert_bookmark_info(self.assertIn, html)
        else:
            self.assert_bookmark_info(self.assertNotIn, html)

    @ddt.unpack
    @ddt.data(
        (True, 0.9, True),
        (False, 0.9, False),
        (True, 1.0, False),
    )
    def test_mark_completed_on_view_after_delay_in_context(
            self, completion_enabled, completion_value, mark_completed_enabled
    ):
        """
        Test that mark-completed-on-view-after-delay is only set for relevant child Xblocks.
        """
        with patch.object(self.html1block, 'render') as mock_student_view:
            self.module_system._services['completion'] = StubCompletionService(
                enabled=completion_enabled,
                completion_value=completion_value,
            )
            self.module_system.render(self.vertical, STUDENT_VIEW, self.default_context)
            if (mark_completed_enabled):
                self.assertEqual(
                    mock_student_view.call_args[0][1]['wrap_xblock_data']['mark-completed-on-view-after-delay'], 9876
                )
            else:
                self.assertNotIn('wrap_xblock_data', mock_student_view.call_args[0][1])

    def test_render_studio_view(self):
        """
        Test the rendering of the Studio author view
        """
        # Vertical shouldn't render children on the unit page
        context = {
            'is_unit_page': True
        }
        html = self.module_system.render(self.vertical, AUTHOR_VIEW, context).content
        self.assertNotIn(self.test_html_1, html)
        self.assertNotIn(self.test_html_2, html)

        # Vertical should render reorderable children on the container page
        reorderable_items = set()
        context = {
            'is_unit_page': False,
            'reorderable_items': reorderable_items,
        }
        html = self.module_system.render(self.vertical, AUTHOR_VIEW, context).content
        self.assertIn(self.test_html_1, html)
        self.assertIn(self.test_html_2, html)
