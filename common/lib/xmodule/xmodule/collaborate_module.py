from lxml import etree
from pkg_resources import resource_string, resource_listdir

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

import json

class CollaborateModule(XModule):
    js = {'coffee':
            [resource_string(__name__, 'js/src/collaborate/display.coffee')]
        }
    js_module_name = "FindCollaborator"
    def get_html(self):
        context = {
            'collaborate_room': self.collaborate_room,
        }
        return self.system.render_template('xmodules/collaborate_module.html', context)

    def __init__(self, system, location, definition, descriptor, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor, instance_state, shared_state, **kwargs)

        if isinstance(instance_state, str):
            instance_state = json.loads(instance_state)
        xml_data = etree.fromstring(definition['data'])
        self.collaborate_room = xml_data.attrib['collaborate_room']

class CollaborateDescriptor(RawDescriptor):
    module_class = CollaborateModule
    template_dir_name = "collaborate"
