import time
import dateutil.parser
import logging

from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor, SequenceModule

log = logging.getLogger(__name__)


class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule

    def __init__(self, system, definition=None, **kwargs):
        super(CourseDescriptor, self).__init__(system, definition, **kwargs)

        try:
            self.start = time.strptime(self.metadata["start"], "%Y-%m-%dT%H:%M")
        except KeyError:
            self.start = time.gmtime(0)  # The epoch
            log.critical("Course loaded without a start date. " + str(self.id))
        except ValueError, e:
            self.start = time.gmtime(0)  # The epoch
            log.critical("Course loaded with a bad start date. " + str(self.id) + " '" + str(e) + "'")

    def has_started(self):
        return time.gmtime() > self.start

    @classmethod
    def id_to_location(cls, course_id):
        org, course, name = course_id.split('/')
        return Location('i4x', org, course, 'course', name)

    @property
    def id(self):
        return "/".join([self.location.org, self.location.course, self.location.name])

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
