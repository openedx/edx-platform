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
import six

from . import get_test_system
from .helpers import StubUserService
from .xml import XModuleXmlImportTest
from .xml import factories as xml
from ..x_module import STUDENT_VIEW, AUTHOR_VIEW


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
    def assert_bookmark_info_in(self, content):
        """
        Assert content has all the bookmark info.
        """
        self.assertIn('bookmark_id', content)
        self.assertIn('{},{}'.format(self.username, unicode(self.vertical.location)), content)
        self.assertIn('bookmarked', content)
        self.assertIn('show_bookmark_button', content)

    @ddt.unpack
    @ddt.data(
        {'context': None},
        {'context': {}}
    )
    def test_render_student_view(self, context):
        """
        Test the rendering of the student view.
        """
        self.module_system._services['bookmarks'] = Mock()
        self.module_system._services['user'] = StubUserService()

        html = self.module_system.render(
            self.vertical, STUDENT_VIEW, self.default_context if context is None else context
        ).content
        self.assertIn(self.test_html_1, html)
        self.assertIn(self.test_html_2, html)
        self.assert_bookmark_info_in(html)

    @staticmethod
    def _render_completable_blocks(template, context):  # pylint: disable=unused-argument
        """
        A custom template rendering function that displays the
        watched_completable_blocks of the template.

        This is used because the default test renderer is haphazardly
        formatted, and is difficult to make assertions about.
        """
        return u'|'.join(context['watched_completable_blocks'])

    @ddt.unpack
    @ddt.data(
        (True, 0.9, 'assertIn'),
        (False, 0.9, 'assertNotIn'),
        (True, 1.0, 'assertNotIn'),
    )
    def test_completion_data_attrs(self, completion_enabled, completion_value, assertion_method):
        """
        Test that data-completable-by-viewing attributes are included only when
        the completion service is enabled, and only for blocks with a
        completion value less than 1.0.
        """
        with patch.object(self.module_system, 'render_template', new=self._render_completable_blocks):
            self.module_system._services['completion'] = StubCompletionService(
                enabled=completion_enabled,
                completion_value=completion_value,
            )
            response = self.module_system.render(self.vertical, STUDENT_VIEW, self.default_context)
        getattr(self, assertion_method)(six.text_type(self.html1block.location), response.content)
        getattr(self, assertion_method)(six.text_type(self.html2block.location), response.content)

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

    def test_publish_completion(self):
        request = get_json_request({"block_key": six.text_type(self.html1block.location), "completion": 1.0})
        with patch.object(self.vertical.runtime, 'publish') as mock_publisher:
            response = self.vertical.publish_completion(request)
            self.assertEqual(
                response.status_code,
                200,
                "Expected 200, got {}: {}".format(response.status_code, response.body),
            )
            mock_publisher.assert_called_with(self.html1block, "completion", {"completion": 1.0})
