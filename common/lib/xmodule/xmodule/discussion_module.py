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
            'threads': comment_client.get_threads(self.discussion_id, recursive=False),
            'time_ago_in_words': time_ago_in_words,
            'parse': dateutil.parser.parse,
            'discussion_id': self.discussion_id,
            'search_bar': '',
        }
        return self.system.render_template('discussion/inline.html', context)

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        xml_data = etree.fromstring(definition['data'])
        self.discussion_id = xml_data.attrib['id']
        self.title = xml_data.attrib['for']
        self.category = xml_data.attrib['category']

class DiscussionDescriptor(RawDescriptor):
    module_class = DiscussionModule
