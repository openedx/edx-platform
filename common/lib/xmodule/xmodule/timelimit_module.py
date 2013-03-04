import json
import logging

from lxml import etree
from time import time

from xmodule.editing_module import XMLEditingDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.progress import Progress
from xmodule.exceptions import NotFoundError


log = logging.getLogger(__name__)

class TimeLimitModule(XModule):
    ''' 
    Wrapper module which imposes a time constraint for the completion of its child.
    '''

    def __init__(self, system, location, definition, descriptor, instance_state=None,
                 shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition, descriptor,
                         instance_state, shared_state, **kwargs)

        self.rendered = False
        self.beginning_at = None
        self.ending_at = None
        self.accommodation_code = None
        
        if instance_state is not None:
            state = json.loads(instance_state)

            if 'beginning_at' in state:
                self.beginning_at = state['beginning_at']
            if 'ending_at' in state:
                self.ending_at = state['ending_at']
            if 'accommodation_code' in state:
                self.accommodation_code = state['accommodation_code']
                
    # For a timed activity, we are only interested here
    # in time-related accommodations, and these should be disjoint.
    # (For proctored exams, it is possible to have multiple accommodations
    # apply to an exam, so they require accommodating a multi-choice.)
    TIME_ACCOMMODATION_CODES = (('NONE', 'No Time Accommodation'),
                      ('ADDHALFTIME', 'Extra Time - 1 1/2 Time'),
                      ('ADD30MIN', 'Extra Time - 30 Minutes'),
                      ('DOUBLE', 'Extra Time - Double Time'),
                      ('TESTING', 'Extra Time -- Large amount for testing purposes')
                    )

    def _get_accommodated_duration(self, duration):
        ''' 
        Get duration for activity, as adjusted for accommodations.
        Input and output are expressed in seconds.
        '''
        if self.accommodation_code is None or self.accommodation_code == 'NONE':
            return duration
        elif self.accommodation_code == 'ADDHALFTIME':
            # TODO:  determine what type to return
            return int(duration * 1.5)
        elif self.accommodation_code == 'ADD30MIN':
            return (duration + (30 * 60))
        elif self.accommodation_code == 'DOUBLE':
            return (duration * 2)
        elif self.accommodation_code == 'TESTING':
            # when testing, set timer to run for a week at a time.
            return 3600 * 24 * 7

    @property
    def has_begun(self):
        return self.beginning_at is not None
    
    @property    
    def has_ended(self):
        if not self.ending_at:
            return False
        return self.ending_at < time()
        
    def begin(self, duration):
        ''' 
        Sets the starting time and ending time for the activity,
        based on the duration provided (in seconds).
        '''
        self.beginning_at = time()
        modified_duration = self._get_accommodated_duration(duration)
        self.ending_at = self.beginning_at + modified_duration
        
    def get_remaining_time_in_ms(self):
        return int((self.ending_at - time()) * 1000)

    def get_instance_state(self):
        state = {}
        if self.beginning_at:
            state['beginning_at'] = self.beginning_at
        if self.ending_at:
            state['ending_at'] = self.ending_at
        if self.accommodation_code:
            state['accommodation_code'] = self.accommodation_code
        return json.dumps(state)

    def get_html(self):
        self.render()
        return self.content

    def get_progress(self):
        ''' Return the total progress, adding total done and total available.
        (assumes that each submodule uses the same "units" for progress.)
        '''
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses)
        return progress

    def handle_ajax(self, dispatch, get):
        raise NotFoundError('Unexpected dispatch type')

    def render(self):
        if self.rendered:
            return
        # assumes there is one and only one child, so it only renders the first child
        children = self.get_display_items()
        if children:
            child = children[0]
            self.content = child.get_html()
        self.rendered = True

    def get_icon_class(self):
        children = self.get_children()
        if children:
            return children[0].get_icon_class()
        else:
            return "other"

class TimeLimitDescriptor(XMLEditingDescriptor, XmlDescriptor):

    module_class = TimeLimitModule

    # For remembering when a student started, and when they should end
    stores_state = True 

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        children = []
        for child in xml_object:
            try:
                children.append(system.process_xml(etree.tostring(child, encoding='unicode')).location.url())
            except Exception as e:
                log.exception("Unable to load child when parsing TimeLimit wrapper. Continuing...")
                if system.error_tracker is not None:
                    system.error_tracker("ERROR: " + str(e))
                continue
        return {'children': children}

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('timelimit')
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object

