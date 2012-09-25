from lxml import etree
from pkg_resources import resource_string, resource_listdir

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

import json

class DiscussionModule(XModule):
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

    def __init__(self, system, location, definition, descriptor, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor, instance_state, shared_state, **kwargs)

        if isinstance(instance_state, str):
            instance_state = json.loads(instance_state)
        xml_data = etree.fromstring(definition['data'])
        self.discussion_id = xml_data.attrib['id']
        self.title = xml_data.attrib['for']
        self.discussion_category = xml_data.attrib['discussion_category']

class DiscussionDescriptor(RawDescriptor):
    module_class = DiscussionModule
    template_dir_name = "discussion"
