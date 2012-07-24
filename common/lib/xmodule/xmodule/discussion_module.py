from lxml import etree

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

import comment_client
import dateutil
from dateutil.tz import tzlocal
from datehelper import time_ago_in_words

import json

class DiscussionModule(XModule):
    def get_html(self):
        context = {
            'threads': comment_client.get_threads(self.discussion_id, recursive=False),
            'time_ago_in_words': time_ago_in_words,
            'parse': dateutil.parser.parse,
            'discussion_id': self.discussion_id,
            'search_bar': '',
            'user_info': comment_client.get_user_info(self.user_id, raw=True),
            'course_id': self.course_id,
        }
        return self.system.render_template('discussion/inline.html', context)

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)

        if isinstance(instance_state, str):
            instance_state = json.loads(instance_state)
        xml_data = etree.fromstring(definition['data'])
        self.discussion_id = xml_data.attrib['id']
        self.title = xml_data.attrib['for']
        self.discussion_category = xml_data.attrib['discussion_category']
        self.user_id = instance_state['user_id']
        self.course_id = instance_state['course_id']

class DiscussionDescriptor(RawDescriptor):
    module_class = DiscussionModule
