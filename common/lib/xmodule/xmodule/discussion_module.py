from lxml import etree

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

import comment_client
import dateutil
from dateutil.tz import tzlocal
from datehelper import time_ago_in_words

class DiscussionModule(XModule):
    def get_html(self):
        context = {
            'threads': comment_client.get_threads(self.discussion_id, recursive=True),
            'time_ago_in_words': time_ago_in_words,
            'parse': dateutil.parser.parse,
        }
        return self.system.render_template('discussion.html', context)

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        xml_data = etree.fromstring(definition['data'])
        self.discussion_id = xml_data.attrib['id']
        self.title = xml_data.attrib['for']

class DiscussionDescriptor(RawDescriptor):
    module_class = DiscussionModule
