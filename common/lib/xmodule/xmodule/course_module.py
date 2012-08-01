from fs.errors import ResourceNotFoundError
import time
import dateutil.parser
import logging

from xmodule.graders import load_grading_policy
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor, SequenceModule

log = logging.getLogger(__name__)


class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule
    metadata_attributes = SequenceDescriptor.metadata_attributes + ('org', 'course')

    def __init__(self, system, definition=None, **kwargs):
        super(CourseDescriptor, self).__init__(system, definition, **kwargs)
        
        self._grader = None
        self._grade_cutoffs = None

        msg = None
        try:
            self.start = time.strptime(self.metadata["start"], "%Y-%m-%dT%H:%M")
        except KeyError:
            self.start = time.gmtime(0) #The epoch
            msg = "Course loaded without a start date. id = %s" % self.id
            log.critical(msg)
        except ValueError as e:
            self.start = time.gmtime(0) #The epoch
            msg = "Course loaded with a bad start date. %s '%s'" % (self.id, e)
            log.critical(msg)

        # Don't call the tracker from the exception handler.
        if msg is not None:
            system.error_tracker(msg)


    def has_started(self):
        return time.gmtime() > self.start
    
    @property
    def grader(self):
        self.__load_grading_policy()
        return self._grader
    
    @property
    def grade_cutoffs(self):
        self.__load_grading_policy()
        return self._grade_cutoffs
    
    
    def __load_grading_policy(self):
        if not self._grader or not self._grade_cutoffs:
            policy_string = ""
            
            try:
                with self.system.resources_fs.open("grading_policy.json") as grading_policy_file:
                    policy_string = grading_policy_file.read()
            except (IOError, ResourceNotFoundError):
                log.warning("Unable to load course settings file from grading_policy.json in course " + self.id)
            
            grading_policy = load_grading_policy(policy_string)
            
            self._grader = grading_policy['GRADER']
            self._grade_cutoffs = grading_policy['GRADE_CUTOFFS']
    
    
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

