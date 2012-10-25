from fs.errors import ResourceNotFoundError
import logging
import json
from lxml import etree
from path import path # NOTE (THK): Only used for detecting presence of syllabus
import requests
import time
from cStringIO import StringIO

from xmodule.util.decorators import lazyproperty
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor, SequenceModule
from xmodule.xml_module import XmlDescriptor
from xmodule.timeparse import parse_time, stringify_time
from xmodule.graders import grader_from_conf

log = logging.getLogger(__name__)

edx_xml_parser = etree.XMLParser(dtd_validation=False, load_dtd=False,
                                 remove_comments=True, remove_blank_text=True)

class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule

    template_dir_name = 'course'

    class Textbook:
        def __init__(self, title, book_url):
            self.title = title
            self.book_url = book_url
            self.table_of_contents = self._get_toc_from_s3()
            self.start_page = int(self.table_of_contents[0].attrib['page'])
            
            # The last page should be the last element in the table of contents,
            # but it may be nested. So recurse all the way down the last element
            last_el = self.table_of_contents[-1]
            while last_el.getchildren():
                last_el = last_el[-1]
            
            self.end_page = int(last_el.attrib['page'])

        @property
        def table_of_contents(self):
            return self.table_of_contents

        def _get_toc_from_s3(self):
            """
            Accesses the textbook's table of contents (default name "toc.xml") at the URL self.book_url

            Returns XML tree representation of the table of contents
            """
            toc_url = self.book_url + 'toc.xml'

            # Get the table of contents from S3
            log.info("Retrieving textbook table of contents from %s" % toc_url)
            try:
                r = requests.get(toc_url)
            except Exception as err:
                msg = 'Error %s: Unable to retrieve textbook table of contents at %s' % (err, toc_url)
                log.error(msg)
                raise Exception(msg)

            # TOC is XML. Parse it
            try:
                table_of_contents = etree.fromstring(r.text)
            except Exception as err:
                msg = 'Error %s: Unable to parse XML for textbook table of contents at %s' % (err, toc_url)
                log.error(msg)
                raise Exception(msg)

            return table_of_contents

    def __init__(self, system, definition=None, **kwargs):
        super(CourseDescriptor, self).__init__(system, definition, **kwargs)
        self.textbooks = []
        for title, book_url in self.definition['data']['textbooks']:
            try:
                self.textbooks.append(self.Textbook(title, book_url))
            except:
                # If we can't get to S3 (e.g. on a train with no internet), don't break
                # the rest of the courseware.
                log.exception("Couldn't load textbook ({0}, {1})".format(title, book_url))
                continue

        self.wiki_slug = self.definition['data']['wiki_slug'] or self.location.course

        msg = None
        if self.start is None:
            msg = "Course loaded without a valid start date. id = %s" % self.id
            # hack it -- start in 1970
            self.metadata['start'] = stringify_time(time.gmtime(0))
            log.critical(msg)
            system.error_tracker(msg)

        self.enrollment_start = self._try_parse_time("enrollment_start")
        self.enrollment_end = self._try_parse_time("enrollment_end")

        # NOTE: relies on the modulestore to call set_grading_policy() right after
        # init.  (Modulestore is in charge of figuring out where to load the policy from)

        # NOTE (THK): This is a last-minute addition for Fall 2012 launch to dynamically
        #   disable the syllabus content for courses that do not provide a syllabus
        self.syllabus_present = self.system.resources_fs.exists(path('syllabus'))

        self.set_grading_policy(self.definition['data'].get('grading_policy', None))


    def set_grading_policy(self, course_policy):
        if course_policy is None:
            course_policy = {}

        """
        The JSON object can have the keys GRADER and GRADE_CUTOFFS. If either is
        missing, it reverts to the default.
        """

        default_policy_string = """
        {
            "GRADER" : [
                {
                    "type" : "Homework",
                    "min_count" : 12,
                    "drop_count" : 2,
                    "short_label" : "HW",
                    "weight" : 0.15
                },
                {
                    "type" : "Lab",
                    "min_count" : 12,
                    "drop_count" : 2,
                    "category" : "Labs",
                    "weight" : 0.15
                },
                {
                    "type" : "Midterm",
                    "name" : "Midterm Exam",
                    "short_label" : "Midterm",
                    "weight" : 0.3
                },
                {
                    "type" : "Final",
                    "name" : "Final Exam",
                    "short_label" : "Final",
                    "weight" : 0.4
                }
            ],
            "GRADE_CUTOFFS" : {
                "A" : 0.87,
                "B" : 0.7,
                "C" : 0.6
            }
        }
        """

        # Load the global settings as a dictionary
        grading_policy = json.loads(default_policy_string)

        # Override any global settings with the course settings
        grading_policy.update(course_policy)

        # Here is where we should parse any configurations, so that we can fail early
        grading_policy['GRADER'] = grader_from_conf(grading_policy['GRADER'])
        self._grading_policy = grading_policy



    @classmethod
    def read_grading_policy(cls, paths, system):
        """Load a grading policy from the specified paths, in order, if it exists."""
        # Default to a blank policy
        policy_str = '""'

        for policy_path in paths:
            if not system.resources_fs.exists(policy_path):
                continue
            log.debug("Loading grading policy from {0}".format(policy_path))
            try:
                with system.resources_fs.open(policy_path) as grading_policy_file:
                    policy_str = grading_policy_file.read()
                    # if we successfully read the file, stop looking at backups
                    break
            except (IOError):
                msg = "Unable to load course settings file from '{0}'".format(policy_path)
                log.warning(msg)

        return policy_str

    
    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        instance = super(CourseDescriptor, cls).from_xml(xml_data, system, org, course)

        # bleh, have to parse the XML here to just pull out the url_name attribute
        course_file = StringIO(xml_data)
        xml_obj = etree.parse(course_file,parser=edx_xml_parser).getroot()

        policy_dir = None
        url_name = xml_obj.get('url_name', xml_obj.get('slug'))
        if url_name:
            policy_dir = 'policies/' + url_name

        # Try to load grading policy
        paths = ['grading_policy.json']
        if policy_dir:
            paths = [policy_dir + 'grading_policy.json'] + paths

        policy = json.loads(cls.read_grading_policy(paths, system))
        
        # cdodge: import the grading policy information that is on disk and put into the
        # descriptor 'definition' bucket as a dictionary so that it is persisted in the DB
        instance.definition['data']['grading_policy'] = policy

        # now set the current instance. set_grading_policy() will apply some inheritance rules
        instance.set_grading_policy(policy)

        return instance
    

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        textbooks = []
        for textbook in xml_object.findall("textbook"):
            textbooks.append((textbook.get('title'), textbook.get('book_url')))
            xml_object.remove(textbook)

        #Load the wiki tag if it exists
        wiki_slug = None
        wiki_tag = xml_object.find("wiki")
        if wiki_tag is not None:
            wiki_slug = wiki_tag.attrib.get("slug", default=None)
            xml_object.remove(wiki_tag)

        definition = super(CourseDescriptor, cls).definition_from_xml(xml_object, system)

        definition.setdefault('data', {})['textbooks'] = textbooks
        definition['data']['wiki_slug'] = wiki_slug

        return definition

    def has_started(self):
        return time.gmtime() > self.start

    @property
    def grader(self):
        return self._grading_policy['GRADER']

    @property
    def grade_cutoffs(self):
        return self._grading_policy['GRADE_CUTOFFS']

    @property
    def tabs(self):
        """
        Return the tabs config, as a python object, or None if not specified.
        """
        return self.metadata.get('tabs')

    @property
    def show_calculator(self):
        return self.metadata.get("show_calculator", None) == "Yes"

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
                    xmoduledescriptors.append(s)

                    # The xmoduledescriptors included here are only the ones that have scores.
                    section_description = { 'section_descriptor' : s, 'xmoduledescriptors' : filter(lambda child: child.has_score, xmoduledescriptors) }

                    section_format = s.metadata.get('format', "")
                    graded_sections[ section_format ] = graded_sections.get( section_format, [] ) + [section_description]

                    all_descriptors.extend(xmoduledescriptors)
                    all_descriptors.append(s)

        return { 'graded_sections' : graded_sections,
                 'all_descriptors' : all_descriptors,}


    @staticmethod
    def make_id(org, course, url_name):
        return '/'.join([org, course, url_name])

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
        """Return the course_id for this course"""
        return self.location_to_id(self.location)

    @property
    def start_date_text(self):
        return time.strftime("%b %d, %Y", self.start)

    # An extra property is used rather than the wiki_slug/number because
    # there are courses that change the number for different runs. This allows
    # courses to share the same css_class across runs even if they have
    # different numbers.
    #
    # TODO get rid of this as soon as possible or potentially build in a robust
    # way to add in course-specific styling. There needs to be a discussion
    # about the right way to do this, but arjun will address this ASAP. Also
    # note that the courseware template needs to change when this is removed.
    @property
    def css_class(self):
        return self.metadata.get('css_class', '')

    @property
    def info_sidebar_name(self):
        return self.metadata.get('info_sidebar_name', 'Course Handouts')

    @property
    def discussion_link(self):
        """TODO: This is a quick kludge to allow CS50 (and other courses) to
        specify their own discussion forums as external links by specifying a
        "discussion_link" in their policy JSON file. This should later get
        folded in with Syllabus, Course Info, and additional Custom tabs in a
        more sensible framework later."""
        return self.metadata.get('discussion_link', None)

    @property
    def hide_progress_tab(self):
        """TODO: same as above, intended to let internal CS50 hide the progress tab
        until we get grade integration set up."""
        # Explicit comparison to True because we always want to return a bool.
        return self.metadata.get('hide_progress_tab') == True

    @property
    def title(self):
        return self.display_name

    @property
    def number(self):
        return self.location.course

    @property
    def org(self):
        return self.location.org


