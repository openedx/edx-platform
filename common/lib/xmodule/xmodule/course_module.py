from fs.errors import ResourceNotFoundError
import time
import dateutil.parser
import logging

from xmodule.util.decorators import lazyproperty
from xmodule.graders import load_grading_policy
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor, SequenceModule

log = logging.getLogger(__name__)


class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule

    def __init__(self, system, definition=None, **kwargs):
        super(CourseDescriptor, self).__init__(system, definition, **kwargs)

        msg = None
        try:
            self.start = time.strptime(self.metadata["start"], "%Y-%m-%dT%H:%M")
        except KeyError:
            msg = "Course loaded without a start date. id = %s" % self.id
        except ValueError as e:
            msg = "Course loaded with a bad start date. %s '%s'" % (self.id, e)

        # Don't call the tracker from the exception handler.
        if msg is not None:
            self.start = time.gmtime(0)  # The epoch
            log.critical(msg)
            system.error_tracker(msg)

        def try_parse_time(key):
            """
            Parse an optional metadata key: if present, must be valid.
            Return None if not present.
            """
            if key in self.metadata:
                try:
                    return time.strptime(self.metadata[key], "%Y-%m-%dT%H:%M")
                except ValueError as e:
                    msg = "Course %s loaded with a bad metadata key %s '%s'" % (
                        self.id, self.metadata[key], e)
                    log.warning(msg)
            return None

        self.enrollment_start = try_parse_time("enrollment_start")
        self.enrollment_end = try_parse_time("enrollment_end")




    def has_started(self):
        return time.gmtime() > self.start

    @property
    def grader(self):
        return self.__grading_policy['GRADER']

    @property
    def grade_cutoffs(self):
        return self.__grading_policy['GRADE_CUTOFFS']

    @lazyproperty
    def __grading_policy(self):
        policy_string = ""

        try:
            with self.system.resources_fs.open("grading_policy.json") as grading_policy_file:
                policy_string = grading_policy_file.read()
        except (IOError, ResourceNotFoundError):
            log.warning("Unable to load course settings file from grading_policy.json in course " + self.id)

        grading_policy = load_grading_policy(policy_string)

        return grading_policy


    @lazyproperty
    def grading_context(self):
        """
        This returns a dictionary with keys necessary for quickly grading
        a student. They are used by grades.grade()

        The grading context has two keys:
        graded_sections - This contains the sections that are graded, as
            well as all possible children modules that can affect the
            grading. This allows some sections to be skipped if the student
            hasn't seen any part of it.

            The format is a dictionary keyed by section-type. The values are
            arrays of dictionaries containing
                "section_descriptor" : The section descriptor
                "xmoduledescriptors" : An array of xmoduledescriptors that
                    could possibly be in the section, for any student

        all_descriptors - This contains a list of all xmodules that can
            effect grading a student. This is used to efficiently fetch
            all the xmodule state for a StudentModuleCache without walking
            the descriptor tree again.


        """

        all_descriptors = []
        graded_sections = {}

        def yield_descriptor_descendents(module_descriptor):
            for child in module_descriptor.get_children():
                yield child
                for module_descriptor in yield_descriptor_descendents(child):
                    yield module_descriptor

        for c in self.get_children():
            sections = []
            for s in c.get_children():
                if s.metadata.get('graded', False):
                    xmoduledescriptors = list(yield_descriptor_descendents(s))

                    # The xmoduledescriptors included here are only the ones that have scores.
                    section_description = { 'section_descriptor' : s, 'xmoduledescriptors' : filter(lambda child: child.has_score, xmoduledescriptors) }

                    section_format = s.metadata.get('format', "")
                    graded_sections[ section_format ] = graded_sections.get( section_format, [] ) + [section_description]

                    all_descriptors.extend(xmoduledescriptors)
                    all_descriptors.append(s)

        return { 'graded_sections' : graded_sections,
                 'all_descriptors' : all_descriptors,}


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
    def wiki_slug(self):
        return self.location.course

    @property
    def org(self):
        return self.location.org

