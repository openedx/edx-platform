# -*- coding: utf-8 -*-
"""
Course Discussion XBlock
"""
import logging

from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment


log = logging.getLogger(__name__)


def _(text):
    """
    A noop underscore function that marks strings for extraction.
    """
    return text


class DiscussionCourseXBlock(XBlock):
    """ Provides functionality similar to discussion XModule in tab mode """
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        default=_("Discussion Course"),
        scope=Scope.settings
    )

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders student view for LMS and Studio """
        return self._get_message_fragment()

    def _get_message_fragment(self):
        """ Returns deprecation message fragment """
        fragment = Fragment()
        fragment.add_content(self.runtime.render_template('discussion/_course_discussion_section.html', {}))
        return fragment

    def studio_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders author view Studio """
        return self._get_message_fragment()
