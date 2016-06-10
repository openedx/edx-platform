# -*- coding: utf-8 -*-
"""
Discussion XBlock
"""
import json
import logging

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from xblock.core import XBlock
from xblock.fields import Scope, String, UNIQUE_ID
from xblock.fragment import Fragment

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


def _(text):
    """A noop underscore function that marks strings for extraction."""
    return text


@XBlock.needs('user')
@XBlock.needs('i18n')
class DiscussionXBlock(XBlock, StudioEditableXBlockMixin):
    """Provides a discussion forum that is inline with other content in the courseware."""

    discussion_id = String(scope=Scope.settings, default=UNIQUE_ID, force_export=True)
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        default="Discussion",
        scope=Scope.settings
    )
    discussion_category = String(
        display_name=_("Category"),
        default=_("Week 1"),
        help=_(
            "A category name for the discussion. "
            "This name appears in the left pane of the discussion forum for the course."
        ),
        scope=Scope.settings
    )
    discussion_target = String(
        display_name=_("Subcategory"),
        default="Topic-Level Student-Visible Label",
        help=_(
            "A subcategory name for the discussion. "
            "This name appears in the left pane of the discussion forum for the course."
        ),
        scope=Scope.settings
    )
    sort_key = String(scope=Scope.settings)

    editable_fields = ["display_name", "discussion_category", "discussion_target"]

    @property
    def course_key(self):
        """
        :return: int course id
        """
        return getattr(self.scope_ids.usage_id, 'course_key', None)

    @property
    def django_user(self):
        """
        Returns django user associated with user currently interacting
        with the XBlock.
        """
        user_service = self.runtime.service(self, 'user')
        if not user_service:
            return None
        return user_service._django_user  # pylint: disable=protected-access

    def has_permission(self, permission):
        """

        Encapsulates lms specific functionality, as `has_permission` is not
        importable outside of lms context, namely in tests.

        :param user:
        :param str permission: Permission
        :rtype: bool
        """
        # normal import causes the xmodule_assets command to fail due to circular import - hence importing locally
        from django_comment_client.permissions import has_permission  # pylint: disable=import-error

        return has_permission(self.django_user, permission, self.course_key)

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders student view for LMS and Studio """
        # pylint: disable=no-member
        if hasattr(self, 'xmodule_runtime') and getattr(self.xmodule_runtime, 'is_author_mode', False):
            return self.student_view_studio()
        else:
            return self.student_view_lms()

    def student_view_lms(self):
        """ Renders student view for LMS """

        fragment = Fragment()

        course = self.runtime.modulestore.get_course(self.course_key)

        context = {
            'discussion_id': self.discussion_id,
            'user': self.django_user,
            'course': course,
            # used as template condition: must be boolean
            'can_create_thread': self.has_permission("create_thread"),
            # used as html data: must be JSON
            'can_create_comment': json.dumps(self.has_permission("create_comment")),
            'can_create_subcomment': json.dumps(self.has_permission("create_subcomment")),
        }

        fragment.add_content(self.runtime.render_template('discussion/_discussion_inline.html', context))
        fragment.add_javascript(loader.render_template('static/discussion_inline.js', {'course_id': self.course_key}))

        fragment.initialize_js('DiscussionInlineBlock')

        return fragment

    def student_view_studio(self):
        """ Renders student view for Studio """
        fragment = Fragment()
        fragment.add_content(self.runtime.render_template(
            'discussion/_discussion_inline_studio.html',
            {'discussion_id': self.discussion_id}
        ))
        return fragment
