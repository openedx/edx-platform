import json
import logging

from lxml import etree
from pkg_resources import resource_string, resource_listdir

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor
from xblock.core import Integer, Scope, Boolean

log = logging.getLogger(__name__)


class PollModule(XModule):

    js = {'coffee': [resource_string(__name__, 'js/src/poll/display.coffee')]}
    js_module_name = "PollModule"

    upvotes = Integer(help="Number of upvotes this poll has recieved", scope=Scope.content, default=0)
    downvotes = Integer(help="Number of downvotes this poll has recieved", scope=Scope.content, default=0)
    voted = Boolean(help="Whether this student has voted on the poll", scope=Scope.student_state, default=False)

    def handle_ajax(self, dispatch, get):
        '''
        Handle ajax calls to this video.
        TODO (vshnayder): This is not being called right now, so the position
        is not being saved.
        '''
        if self.voted:
            return json.dumps({'error': 'Already Voted!'})
        elif dispatch == 'upvote':
            self.upvotes += 1
            self.voted = True
            return json.dumps({'results': self.get_html()})
        elif dispatch == 'downvote':
            self.downvotes += 1
            self.voted = True
            return json.dumps({'results': self.get_html()})

        return json.dumps({'error': 'Unknown Command!'})

    def get_html(self):
        return self.system.render_template('poll.html', {
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'voted': self.voted,
            'ajax_url': self.system.ajax_url,
        })


class PollDescriptor(RawDescriptor):
    module_class = PollModule
    stores_state = True
    template_dir_name = "poll"