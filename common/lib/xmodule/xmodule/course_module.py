import logging
from path import path
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor, SequenceModule
from fs.errors import ResourceNotFoundError

log = logging.getLogger(__name__)


class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule

    @classmethod
    def id_to_location(cls, course_id):
        org, course, name = course_id.split('/')
        return Location('i4x', org, course, 'course', name)

    @property
    def id(self):
        return "/".join([self.location.org, self.location.course, self.location.name])

    @property
    def title(self):
        self.metadata['display_name']

    @property
    def instructors(self):
        return self.get_about_section("instructors").split("\n")

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

        # TODO: Remove number, instructors from this list
        if section_key in ['short_description', 'description', 'key_dates', 'video', 'course_staff_short', 'course_staff_extended',
                            'requirements', 'syllabus', 'textbook', 'faq', 'more_info', 'number', 'instructors']:
            try:
                with self.system.resources_fs.open(path("about") / section_key + ".html") as htmlFile:
                    return htmlFile.read()
            except ResourceNotFoundError:
                log.exception("Missing about section {key} in course {url}".format(key=section_key, url=self.location.url()))
                return "! About section missing !"
        elif section_key == "title":
            return self.metadata.get('display_name', self.name)
        elif section_key == "university":
            return self.location.org
        elif section_key == "number":
            return self.number

        raise KeyError("Invalid about key " + str(section_key))

    def get_info_section(self, section_key):
        """
        This returns the snippet of html to be rendered on the course info page, given the key for the section.
        Valid keys:
        - handouts
        - guest_handouts
        - updates
        - guest_updates
        """

        # Many of these are stored as html files instead of some semantic markup. This can change without effecting
        # this interface when we find a good format for defining so many snippets of text/html.

        if section_key in ['handouts', 'guest_handouts', 'updates', 'guest_updates']:
            try:
                with self.system.resources_fs.open(path("info") / section_key + ".html") as htmlFile:
                    return htmlFile.read()
            except ResourceNotFoundError:
                log.exception("Missing info section {key} in course {url}".format(key=section_key, url=self.location.url()))
                return "! About section missing !"

        raise KeyError("Invalid about key " + str(section_key))
