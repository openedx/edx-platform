"""
Definition of the Discussion module.
"""
import json
from pkg_resources import resource_string

from xblock.core import XBlock
from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xblock.fields import String, Scope, UNIQUE_ID

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text


class DiscussionFields(object):
    discussion_id = String(
        display_name=_("Discussion Id"),
        help=_("The id is a unique identifier for the discussion. It is non editable."),
        scope=Scope.settings,
        default=UNIQUE_ID)
    display_name = String(
        display_name=_("Display Name"),
        help=_("Display name for this module"),
        default="Discussion",
        scope=Scope.settings
    )
    data = String(
        help=_("XML data for the problem"),
        scope=Scope.content,
        default="<discussion></discussion>"
    )
    discussion_category = String(
        display_name=_("Category"),
        default="Week 1",
        help=_("A category name for the discussion. This name appears in the left pane of the discussion forum for the course."),
        scope=Scope.settings
    )
    discussion_target = String(
        display_name=_("Subcategory"),
        default="Topic-Level Student-Visible Label",
        help=_("A subcategory name for the discussion. This name appears in the left pane of the discussion forum for the course."),
        scope=Scope.settings
    )
    sort_key = String(scope=Scope.settings)


def has_permission(user, permission, course_id):
    """
    Copied from django_comment_client/permissions.py because I can't import
    that file from here. It causes the xmodule_assets command to fail.
    """
    return any(role.has_permission(permission)
               for role in user.roles.filter(course_id=course_id))


@XBlock.wants('user')
class DiscussionModule(DiscussionFields, XModule):
    """
    XModule for discussion forums.
    """
    js = {
        'coffee': [
            resource_string(__name__, 'js/src/discussion/display.coffee')
        ],
        'js': [
            resource_string(__name__, 'js/src/time.js')
        ]
    }
    js_module_name = "InlineDiscussion"

    def get_html(self):
        course = self.get_course()
        user = None
        user_service = self.runtime.service(self, 'user')
        if user_service:
            user = user_service._django_user  # pylint: disable=protected-access
        if user:
            course_key = course.id
            can_create_comment = has_permission(user, "create_comment", course_key)
            can_create_subcomment = has_permission(user, "create_sub_comment", course_key)
            can_create_thread = has_permission(user, "create_thread", course_key)
        else:
            can_create_comment = False
            can_create_subcomment = False
            can_create_thread = False
        context = {
            'discussion_id': self.discussion_id,
            'course': course,
            'can_create_comment': json.dumps(can_create_comment),
            'can_create_subcomment': json.dumps(can_create_subcomment),
            'can_create_thread': can_create_thread,
        }
        if getattr(self.system, 'is_author_mode', False):
            template = 'discussion/_discussion_module_studio.html'
        else:
            template = 'discussion/_discussion_module.html'
        return self.system.render_template(template, context)

    def get_course(self):
        """
        Return CourseDescriptor by course id.
        """
        course = self.runtime.modulestore.get_course(self.course_id)
        return course


class DiscussionDescriptor(DiscussionFields, MetadataOnlyEditingDescriptor, RawDescriptor):

    module_class = DiscussionModule
    # The discussion XML format uses `id` and `for` attributes,
    # but these would overload other module attributes, so we prefix them
    # for actual use in the code
    metadata_translations = dict(RawDescriptor.metadata_translations)
    metadata_translations['id'] = 'discussion_id'
    metadata_translations['for'] = 'discussion_target'

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(DiscussionDescriptor, self).non_editable_metadata_fields
        # We may choose to enable sort_keys in the future, but while Kevin is investigating....
        non_editable_fields.extend([DiscussionDescriptor.discussion_id, DiscussionDescriptor.sort_key])
        return non_editable_fields
