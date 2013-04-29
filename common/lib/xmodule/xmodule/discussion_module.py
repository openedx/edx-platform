from pkg_resources import resource_string

from xmodule.x_module import XModule, XModuleFields
from xmodule.raw_module import RawDescriptor
from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xblock.core import String, Scope


class DiscussionFields(object):
    discussion_id = String(scope=XModuleFields.nonEditableSettingsScope)
    discussion_category = String(display_name="Category Name", scope=Scope.settings)
    discussion_target = String(display_name="Subcategory Name", scope=Scope.settings)
    # We may choose to enable this in the future, but while Kevin is investigating....
    sort_key = String(scope=XModuleFields.nonEditableSettingsScope)


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
    template_dir_name = "discussion"

    # The discussion XML format uses `id` and `for` attributes,
    # but these would overload other module attributes, so we prefix them
    # for actual use in the code
    metadata_translations = dict(RawDescriptor.metadata_translations)
    metadata_translations['id'] = 'discussion_id'
    metadata_translations['for'] = 'discussion_target'
