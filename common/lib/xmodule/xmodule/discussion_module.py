from lxml import etree
from pkg_resources import resource_string, resource_listdir

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from .model import String, Scope

class DiscussionModule(XModule):
    js = {'coffee':
            [resource_string(__name__, 'js/src/time.coffee'),
            resource_string(__name__, 'js/src/discussion/display.coffee')]
        }
    js_module_name = "InlineDiscussion"

    discussion_id = String(scope=Scope.settings)
    discussion_category = String(scope=Scope.settings)
    discussion_target = String(scope=Scope.settings)
    sort_key = String(scope=Scope.settings)

    data = String(help="XML definition of inline discussion", scope=Scope.content)

    def get_html(self):
        context = {
            'discussion_id': self.discussion_id,
        }
        return self.system.render_template('discussion/_discussion_module.html', context)

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)

        xml_data = etree.fromstring(self.data)
        self.discussion_id = xml_data.attrib['id']
        self.title = xml_data.attrib['for']
        self.discussion_category = xml_data.attrib['discussion_category']

class DiscussionDescriptor(RawDescriptor):
    module_class = DiscussionModule
    template_dir_name = "discussion"

    # The discussion XML format uses `id` and `for` attributes,
    # but these would overload other module attributes, so we prefix them
    # for actual use in the code
    metadata_translations = dict(RawDescriptor.metadata_translations)
    metadata_translations['id'] = 'discussion_id'
    metadata_translations['for'] = 'discussion_target'

    discussion_id = String(scope=Scope.settings)
    discussion_category = String(scope=Scope.settings)
    discussion_target = String(scope=Scope.settings)
    sort_key = String(scope=Scope.settings)
