import json
import logging

from lxml import etree

from pkg_resources import resource_string
from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

from django import forms

log = logging.getLogger(__name__)


class SurveyForm(forms.Form):
    name_f=forms.CharField()
    pass

class SurveyModule(XModule):
    video_time = 0
    icon_class = 'video'

    js = {'coffee': [resource_string(__name__, 'js/src/survey/display.coffee')]}
    js_module_name = "Survey"

    css = {'scss': [resource_string(__name__, 'css/capa/display.scss')]}

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, instance_state, shared_state, **kwargs)
        xmltree = etree.fromstring(self.definition['data'])
        self.name = xmltree.get('title')
        #getting a list of questions for each survey element:
        self.question_list = []
        for item in list(xmltree):
            # self.question_list.append[{'type':item.get('type'),'question_name':item.get('question_name'),'label':item.get('label')}]
            dic = {'type':item.get('type'),'question_name':item.get('question_name'),'label':item.get('label')}
            self.question_list.append(dic)          
        self.form_to_serve=SurveyForm()


  # <section format="Video" name="Welcome">
  #     <video youtube="0.75:izygArpw-Qo,1.0:p2Q6BrNhdh8,1.25:1EeWXzPdhSA,1.50:rABDYkeK0x8"/>
  # </section>  
    # def get_html(self):
    #     return self.system.render_template('problem_ajax.html', {
    #         'element_id': self.location.html_id(),
    #         'id': self.id,
    #         'ajax_url': self.system.ajax_url,
    #     })

    def handle_ajax(self, dispatch, get):
                
        log.debug(u"GET {0}".format(get))
        log.debug(u"DISPATCH {0}".format(dispatch))
        
        handlers = {
                    'survey_save': self.save_survey
                    }


        if dispatch not in handlers:
            print 'Error dispatch not in handlers'
            return 'Error'

        # return json.dumps(d, cls=ComplexEncoder)


        print "handling dispatch"
        print dispatch
        print get

    # def get_progress(self):
    #     ''' TODO (vshnayder): Get and save duration of youtube video, then return
    #     fraction watched.
    #     (Be careful to notice when video link changes and update)

    #     For now, we have no way of knowing if the video has even been watched, so
    #     just return None.
    #     '''
    #     return None

    # def get_instance_state(self):
    #     return self.state

    def save_survey(self, request):
        print "request recieved"
        return None

    def survey_question_list(self):
        return self.question_list
#dirty test:
    def survey_context(self):
        self.context = {'element_id': self.location.html_id(),
                        'id': self.id,
                        'ajax_url': self.system.ajax_url,
                        'took_survey' : False,
                        'survey_list' : self.survey_question_list(),
                        'survey_name' : self.name}
        return self.context

    def get_html(self):
        print "serving survey"
        return self.system.render_template('survey.html', {"form": self.form_to_serve,
            "id": self.id,
            "ajax_url": self.system.ajax_url,
            "element_id": "some_element_id"})


class SurveyDescriptor(RawDescriptor):
    module_class = SurveyModule
