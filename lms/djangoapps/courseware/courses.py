from collections import namedtuple
import logging
import os

from path import path
import yaml

log = logging.getLogger('mitx.courseware.courses')

_FIELDS = ['number', # 6.002x
           'title', # Circuits and Electronics
           'short_title', # Circuits
           'run_id', # Spring 2012
           'path', # /some/absolute/filepath/6.002x --> course.xml is in here.
           'instructors', # ['Anant Agarwal']
           'institution', # "MIT"
           'grader', # a courseware.graders.CourseGrader object
           'location',

           #'start', # These should be datetime fields
           #'end'
           ]

class CourseInfoLoadError(Exception):
    pass

class Course(namedtuple('Course', _FIELDS)):
    """Course objects encapsulate general information about a given run of a
    course. This includes things like name, grading policy, etc.
    """

    @property
    def id(self):
        return "{0.institution},{0.number},{0.run_id}".format(self).replace(" ", "_")

    @property
    def name(self):
        return "{0.number} {0.run_id}".format(self)

    @classmethod
    def load_from_path(cls, course_path):
        course_path = path(course_path) # convert it from string if necessary
        try:
            with open(course_path / "course_info.yaml") as course_info_file:
                course_info = yaml.load(course_info_file)
            summary = course_info['course']
            summary.update(path=course_path, grader=None)
            return cls(**summary)
        except Exception as ex:
            log.exception(ex)
            raise CourseInfoLoadError("Could not read course info: {0}:{1}"
                                      .format(type(ex).__name__, ex))



    def get_about_section(self, section_key):
        """
        This returns the snippet of html to be rendered on the course about page, given the key for the section.
        Valid keys:
        - title
        - university
        - number
        - short_description
        - description
        - key_dates (includes start, end, exams, etc)
        - video
        - course_staff_short
        - course_staff_extended
        - requirements
        - syllabus
        - textbook
        - faq
        - more_info
        """

        # Many of these are stored as html files instead of some semantic markup. This can change without effecting
        # this interface when we find a good format for defining so many snippets of text/html.

        if section_key in ['short_description', 'description', 'key_dates', 'video', 'course_staff_short', 'course_staff_extended',
                            'requirements', 'syllabus', 'textbook', 'faq', 'more_info']:
            try:
                with open(self.path / "about" / section_key + ".html") as htmlFile:
                    return htmlFile.read()
            except IOError:
                return "! About section missing !"
        elif section_key == "title":
            return self.title
        elif section_key == "university":
            return self.institution
        elif section_key == "number":
            return self.number

        raise KeyError("Invalid about key " + str(section_key))

def load_courses(courses_path):
    """Given a directory of courses, returns a list of Course objects. For the
    sake of backwards compatibility, if you point it at the top level of a
    specific course, it will return a list with one Course object in it.
    """
    courses_path = path(courses_path)
    def _is_course_path(p):
        return os.path.exists(p / "course_info.yaml")

    log.info("Loading courses from {0}".format(courses_path))

    # Compatibility: courses_path is the path for a single course
    if _is_course_path(courses_path):
        log.warning("course_info.yaml found in top-level ({0})"
                    .format(courses_path) +
                    " -- assuming there is only a single course.")
        return [Course.load_from_path(courses_path)]

    # Default: Each dir in courses_path is a separate course
    courses = []
    log.info("Reading courses from {0}".format(courses_path))
    for course_dir_name in os.listdir(courses_path):
        course_path = courses_path / course_dir_name
        if _is_course_path(course_path):
            log.info("Initializing course {0}".format(course_path))
            courses.append(Course.load_from_path(course_path))

    return courses

def create_lookup_table(courses):
    return dict((c.id, c) for c in courses)
