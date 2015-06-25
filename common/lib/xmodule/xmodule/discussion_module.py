from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xblock.fields import String, Scope, UNIQUE_ID
from uuid import uuid4

# Make '_' a no-op so we can scrape strings
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


class DiscussionModule(DiscussionFields, XModule):
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
        context = {
            'discussion_id': self.discussion_id,
            'course': self.get_course(),
        }
        if getattr(self.system, 'is_author_mode', False):
            template = 'discussion/_discussion_module_studio.html'
        else:
            template = 'discussion/_discussion_module.html'
        return self.system.render_template(template, context)

    def get_course(self):
        """
        Return course by course id.
        """
        return self.descriptor.runtime.modulestore.get_course(self.course_id)


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
