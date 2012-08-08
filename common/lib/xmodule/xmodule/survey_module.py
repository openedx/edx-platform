import datetime
import dateutil
import dateutil.parser
import json
import logging
import traceback
import re

from datetime import timedelta
from lxml import etree
from pkg_resources import resource_string

from xmodule.capa_module import CapaModule, only_one, ComplexEncoder
from xmodule.raw_module import RawDescriptor
from xmodule.exceptions import NotFoundError
from progress import Progress
from capa.capa_problem import LoncapaProblem
from capa.responsetypes import StudentInputError

log = logging.getLogger(__name__)

class SurveyModule(CapaModule):
    """This is a subclass of CapaModule that sets sensible
    default behavior of a problem for surveying students

    Defaults:
        -Never Show Answer, no max attempts 
        -No due date unless specified
        -Only show save button or no buttons

    """

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        CapaModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
    
        # no maximum number of attempts so students can
        # always answer surveys
        # if we're interested in cut-off dates, we can use 
        # the "modified" field from the database
        self.max_attempts = None

        # there is no correct answer, never show one or the button
        self.show_answer = "never"

    def get_problem_html(self, encapsulate=True):
        '''Similiar to the parent class method from CapaModule
        but never shows "check answer"
        '''

        try:
            html = self.lcp.get_html()
        except Exception, err:
            if self.system.DEBUG:
                log.exception(err)
                msg = (
                    '[courseware.capa.capa_module] <font size="+1" color="red">'
                    'Failed to generate HTML for problem %s</font>' %
                    (self.location.url()))
                msg += '<p>Error:</p><p><pre>%s</pre></p>' % str(err).replace('<', '&lt;')
                msg += '<p><pre>%s</pre></p>' % traceback.format_exc().replace('<', '&lt;')
                html = msg
            else:
                raise

        content = {'name': self.metadata['display_name'],
                   'html': html,
                   'weight': self.weight,
                  }

        check_button = False
        reset_button = False
        save_button = True

        # If we're after deadline survey is read-only.
        if self.closed():
            save_button = False

        context = {'problem': content,
                   'id': self.id,
                   'check_button': check_button,
                   'reset_button': reset_button,
                   'save_button': save_button,
                   'answer_available': self.answer_available(),
                   'ajax_url': self.system.ajax_url,
                   'attempts_used': self.attempts,
                   'attempts_allowed': self.max_attempts,
                   'progress': self.get_progress(),
                   }

        html = self.system.render_template('problem.html', context)
        if encapsulate:
            html = '<div id="problem_{id}" class="problem" data-url="{ajax_url}">'.format(
                id=self.location.html_id(), ajax_url=self.system.ajax_url) + html + "</div>"

        return self.system.replace_urls(html, self.metadata['data_dir'])

class SurveyDescriptor(RawDescriptor):
    module_class = SurveyModule
