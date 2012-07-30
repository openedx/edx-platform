import time
import dateutil.parser
import logging

from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor, SequenceModule

log = logging.getLogger(__name__)


class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule
    metadata_attributes = SequenceDescriptor.metadata_attributes + ('org', 'course')

    def __init__(self, system, definition=None, **kwargs):
        super(CourseDescriptor, self).__init__(system, definition, **kwargs)

        try:
            self.start = time.strptime(self.metadata["start"], "%Y-%m-%dT%H:%M")
        except KeyError:
            self.start = time.gmtime(0) #The epoch
            log.critical("Course loaded without a start date. %s", self.id)
        except ValueError as e:
            self.start = time.gmtime(0) #The epoch
            log.critical("Course loaded with a bad start date. %s '%s'",
                         self.id, e)

    def has_started(self):
        return time.gmtime() > self.start

    @staticmethod
    def id_to_location(course_id):
        '''Convert the given course_id (org/course/name) to a location object.
        Throws ValueError if course_id is of the wrong format.
        '''
        org, course, name = course_id.split('/')
        return Location('i4x', org, course, 'course', name)

    @staticmethod
    def location_to_id(location):
        '''Convert a location of a course to a course_id.  If location category
        is not "course", raise a ValueError.

        location: something that can be passed to Location
        '''
        loc = Location(location)
        if loc.category != "course":
            raise ValueError("{0} is not a course location".format(loc))
        return "/".join([loc.org, loc.course, loc.name])


    @property
    def id(self):
        return self.location_to_id(self.location)

    @property
    def start_date_text(self):
        return time.strftime("%b %d, %Y", self.start)

    @property
    def title(self):
        return self.metadata['display_name']

    @property
    def number(self):
        return self.location.course

    @property
    def wiki_namespace(self):
        return self.location.course

    @property
    def org(self):
        return self.location.org
