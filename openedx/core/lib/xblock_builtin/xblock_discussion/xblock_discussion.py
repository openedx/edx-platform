# -*- coding: utf-8 -*-
"""
Discussion XBlock
"""
import logging

from django.templatetags.static import static
from django.utils.translation import get_language_bidi

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from xblock.core import XBlock
from xblock.fields import Scope, String, UNIQUE_ID
from xblock.fragment import Fragment

from openedx.core.lib.xblock_builtin import get_css_dependencies, get_js_dependencies


log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)  # pylint: disable=invalid-name


def _(text):
    """
    A noop underscore function that marks strings for extraction.
    """
    return text


@XBlock.needs('user')
@XBlock.needs('i18n')
class DiscussionXBlock(XBlock, StudioEditableXBlockMixin):
    """
    Provides a discussion forum that is inline with other content in the courseware.
    """
    discussion_id = String(scope=Scope.settings, default=UNIQUE_ID, force_export=True)
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this component"),
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

    has_author_view = True  # Tells Studio to use author_view

    @property
    def course_key(self):
        """
        :return: int course id

        NB: The goal is to move this XBlock out of edx-platform, and so we use
        scope_ids.usage_id instead of runtime.course_id so that the code will
        continue to work with workbench-based testing.
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

    @staticmethod
    def vendor_js_dependencies():
        """
        Returns list of vendor JS files that this XBlock depends on.

        The helper function that it uses to obtain the list of vendor JS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        return get_js_dependencies('discussion_vendor')

    @staticmethod
    def js_dependencies():
        """
        Returns list of JS files that this XBlock depends on.

        The helper function that it uses to obtain the list of JS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        return get_js_dependencies('discussion')

    @staticmethod
    def css_dependencies():
        """
        Returns list of CSS files that this XBlock depends on.

        The helper function that it uses to obtain the list of CSS files
        works in conjunction with the Django pipeline to ensure that in development mode
        the files are loaded individually, but in production just the single bundle is loaded.
        """
        if get_language_bidi():
            return get_css_dependencies('style-inline-discussion-rtl')
        else:
            return get_css_dependencies('style-inline-discussion')

    def add_resource_urls(self, fragment):
        """
        Adds URLs for JS and CSS resources that this XBlock depends on to `fragment`.
        """
        for vendor_js_file in self.vendor_js_dependencies():
            fragment.add_resource_url(static(vendor_js_file), "application/javascript", "head")

        for css_file in self.css_dependencies():
            fragment.add_css_url(static(css_file))

        # Body dependencies
        for js_file in self.js_dependencies():
            fragment.add_javascript_url(static(js_file))

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

    def student_view(self, context=None):
        """
        Renders student view for LMS.
        """
        fragment = Fragment()

        self.add_resource_urls(fragment)

        context = {
            'discussion_id': self.discussion_id,
            'user': self.django_user,
            'course_id': self.course_key,
            'can_create_thread': self.has_permission("create_thread"),
            'can_create_comment': self.has_permission("create_comment"),
            'can_create_subcomment': self.has_permission("create_sub_comment"),
        }

        fragment.add_content(self.runtime.render_template('discussion/_discussion_inline.html', context))
        fragment.initialize_js('DiscussionInlineBlock')

        return fragment

    def author_view(self, context=None):  # pylint: disable=unused-argument
        """
        Renders author view for Studio.
        """
        fragment = Fragment()
        fragment.add_content(self.runtime.render_template(
            'discussion/_discussion_inline_studio.html',
            {'discussion_id': self.discussion_id}
        ))
        return fragment

    def student_view_data(self):
        """
        Returns a JSON representation of the student_view of this XBlock.
        """
        return {'topic_id': self.discussion_id}
