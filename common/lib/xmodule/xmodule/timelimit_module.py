import logging

from lxml import etree
from time import time

from xmodule.editing_module import XMLEditingDescriptor
from xmodule.xml_module import XmlDescriptor
from xmodule.x_module import XModule
from xmodule.progress import Progress
from xmodule.exceptions import NotFoundError
from xblock.fields import Float, String, Boolean, Scope
from xblock.fragment import Fragment


log = logging.getLogger(__name__)


class TimeLimitFields(object):
    has_children = True

    beginning_at = Float(help="The time this timer was started", scope=Scope.user_state)
    ending_at = Float(help="The time this timer will end", scope=Scope.user_state)
    accomodation_code = String(help="A code indicating accommodations to be given the student", scope=Scope.user_state)
    time_expired_redirect_url = String(help="Url to redirect users to after the timelimit has expired", scope=Scope.settings)
    duration = Float(help="The length of this timer", scope=Scope.settings)
    suppress_toplevel_navigation = Boolean(help="Whether the toplevel navigation should be suppressed when viewing this module", scope=Scope.settings)


class TimeLimitModule(TimeLimitFields, XModule):
    '''
    Wrapper module which imposes a time constraint for the completion of its child.
    '''

    def __init__(self, *args, **kwargs):
        XModule.__init__(self, *args, **kwargs)

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

    def student_view(self, context):
        # assumes there is one and only one child, so it only renders the first child
        children = self.get_display_items()
        if children:
            child = children[0]
            return child.render('student_view', context)
        else:
            return Fragment()

    def get_progress(self):
        ''' Return the total progress, adding total done and total available.
        (assumes that each submodule uses the same "units" for progress.)
        '''
        # TODO: Cache progress or children array?
        children = self.get_children()
        progresses = [child.get_progress() for child in children]
        progress = reduce(Progress.add_counts, progresses)
        return progress

    def handle_ajax(self, _dispatch, _data):
        raise NotFoundError('Unexpected dispatch type')

    def get_icon_class(self):
        children = self.get_children()
        if children:
            return children[0].get_icon_class()
        else:
            return "other"

class TimeLimitDescriptor(TimeLimitFields, XMLEditingDescriptor, XmlDescriptor):

    module_class = TimeLimitModule

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
        return {}, children

    def definition_to_xml(self, resource_fs):
        xml_object = etree.Element('timelimit')
        for child in self.get_children():
            xml_object.append(
                etree.fromstring(child.export_to_xml(resource_fs)))
        return xml_object
