import logging

from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from xblock.core import XBlock
from xblock.fields import Scope, String, UNIQUE_ID
from xblock.fragment import Fragment

log = logging.getLogger(__name__)
loader = ResourceLoader(__name__)


@XBlock.needs('user')
class DiscussionXBlock(XBlock, StudioEditableXBlockMixin):
    """ Provides functionality similar to discussion XModule in inline mode """

    discussion_id = String(scope=Scope.settings, default=UNIQUE_ID, force_export=True)
    display_name = String(
        display_name="Display Name",
        help="Display name for this module",
        default="Discussion",
        scope=Scope.settings
    )
    discussion_category = String(
        display_name="Category",
        default="Week 1",
        help="A category name for the discussion. "
             "This name appears in the left pane of the discussion forum for the course.",
        scope=Scope.settings
    )
    discussion_target = String(
        display_name="Subcategory",
        default="Topic-Level Student-Visible Label",
        help="A subcategory name for the discussion. "
             "This name appears in the left pane of the discussion forum for the course.",
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

    def student_view(self, context=None):  # pylint: disable=unused-argument
        """ Renders student view for LMS and Studio """
        # pylint: disable=no-member
        if hasattr(self, 'xmodule_runtime') and getattr(self.xmodule_runtime, 'is_author_mode', False):
            fragment = self._student_view_studio()
        else:
            fragment = self._student_view_lms()

        return fragment

    def _student_view_lms(self):
        """ Renders student view for LMS """
        fragment = Fragment()

        # normal import causes the xmodule_assets command to fail due to circular import - hence importing locally
        from django_comment_client.permissions import has_permission

        user = None
        user_service = self.runtime.service(self, 'user')
        if user_service:
            user = user_service._django_user  # pylint: disable=protected-access

        course = self.runtime.modulestore.get_course(self.course_key)

        context = {
            'discussion_id': self.discussion_id,
            'user': user,
            'course': course,
            'can_create_thread': has_permission(user, "create_thread", self.course_key),
            'can_create_comment': has_permission(user, "create_comment", self.course_key),
            'can_create_subcomment': has_permission(user, "create_subcomment", self.course_key),
        }

        fragment.add_content(self.runtime.render_template('discussion/_discussion_inline.html', context))
        fragment.add_javascript(loader.render_template('static/discussion_inline.js', {'course_id': self.course_key}))

        fragment.initialize_js('DiscussionInlineBlock')

        return fragment

    def _student_view_studio(self):
        """ Renders student view for Studio """
        fragment = Fragment()
        fragment.add_content(self.runtime.render_template(
            'discussion/_discussion_inline_studio.html',
            {'discussion_id': self.discussion_id}
        ))
        return fragment
