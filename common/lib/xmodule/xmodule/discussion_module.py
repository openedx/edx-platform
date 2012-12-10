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
