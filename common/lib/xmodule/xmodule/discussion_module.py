from pkg_resources import resource_string

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xblock.core import String, Scope


class DiscussionFields(object):
    # TODO default to a guid
    discussion_id = String(scope=Scope.settings, default="Week 1")
    discussion_category = String(scope=Scope.settings)
    discussion_target = String(scope=Scope.settings, default="Topic-Level Student-Visible Label")
    display_name = String(help="Display name for this module", default="Discussion Tag", scope=Scope.settings)
    data = String(help="XML data for the problem", scope=Scope.content,
        default="<discussion></discussion>")
    sort_key = String(scope=Scope.settings)


class DiscussionModule(DiscussionFields, XModule):
    js = {'coffee':
          [resource_string(__name__, 'js/src/time.coffee'),
          resource_string(__name__, 'js/src/discussion/display.coffee')]
          }
    js_module_name = "InlineDiscussion"

    def get_html(self):
        context = {
            'discussion_id': self.discussion_id,
        }
        return self.system.render_template('discussion/_discussion_module.html', context)


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
