from cStringIO import StringIO
from lxml import etree
from path import path # NOTE (THK): Only used for detecting presence of syllabus
from xmodule.graders import grader_from_conf
from xmodule.modulestore import Location
from xmodule.seq_module import SequenceDescriptor, SequenceModule
from xmodule.timeparse import parse_time
from xmodule.util.decorators import lazyproperty
import json
import logging
import requests
import time
import copy

from xblock.core import Scope, ModelType, List, String, Object, Boolean
from .fields import Date

log = logging.getLogger(__name__)

edx_xml_parser = etree.XMLParser(dtd_validation=False, load_dtd=False,
                                 remove_comments=True, remove_blank_text=True)

class Textbook(object):
    def __init__(self, title, book_url):
        self.title = title
        self.book_url = book_url
        self.start_page = int(self.table_of_contents[0].attrib['page'])

        # The last page should be the last element in the table of contents,
        # but it may be nested. So recurse all the way down the last element
        last_el = self.table_of_contents[-1]
        while last_el.getchildren():
            last_el = last_el[-1]

        self.end_page = int(last_el.attrib['page'])

    @lazyproperty
    def table_of_contents(self):
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


class TextbookList(ModelType):
    def from_json(self, values):
        textbooks = []
        for title, book_url in values:
            try:
                textbooks.append(Textbook(title, book_url))
            except:
                # If we can't get to S3 (e.g. on a train with no internet), don't break
                # the rest of the courseware.
                log.exception("Couldn't load textbook ({0}, {1})".format(title, book_url))
                continue

        return textbooks

    def to_json(self, values):
        json_data = []
        for val in values:
            if isinstance(val, Textbook):
                json_data.append((textbook.title, textbook.book_url))
            elif isinstance(val, tuple):
                json_data.append(val)
            else:
                continue
        return json_data


class CourseDescriptor(SequenceDescriptor):
    module_class = SequenceModule

    textbooks = TextbookList(help="List of pairs of (title, url) for textbooks used in this course", default=[], scope=Scope.content)
    wiki_slug = String(help="Slug that points to the wiki for this course", scope=Scope.content)
    enrollment_start = Date(help="Date that enrollment for this class is opened", scope=Scope.settings)
    enrollment_end = Date(help="Date that enrollment for this class is closed", scope=Scope.settings)
    start = Date(help="Start time when this module is visible", scope=Scope.settings)
    end = Date(help="Date that this class ends", scope=Scope.settings)
    advertised_start = Date(help="Date that this course is advertised to start", scope=Scope.settings)
    grading_policy = Object(help="Grading policy definition for this class", scope=Scope.content, default={})
    show_calculator = Boolean(help="Whether to show the calculator in this course", default=False, scope=Scope.settings)
    display_name = String(help="Display name for this module", scope=Scope.settings)
    tabs = List(help="List of tabs to enable in this course", scope=Scope.settings)
    end_of_course_survey_url = String(help="Url for the end-of-course survey", scope=Scope.settings)
    discussion_blackouts = List(help="List of pairs of start/end dates for discussion blackouts", scope=Scope.settings, default=[])
    discussion_topics = Object(
        help="Map of topics names to ids",
        scope=Scope.settings,
        computed_default=lambda c: {'General': {'id': c.location.html_id()}},
        )
    has_children = True

    info_sidebar_name = String(scope=Scope.settings, default='Course Handouts')
    
    # An extra property is used rather than the wiki_slug/number because
    # there are courses that change the number for different runs. This allows
    # courses to share the same css_class across runs even if they have
    # different numbers.
    #
    # TODO get rid of this as soon as possible or potentially build in a robust
    # way to add in course-specific styling. There needs to be a discussion
    # about the right way to do this, but arjun will address this ASAP. Also
    # note that the courseware template needs to change when this is removed.
    css_class = String(help="DO NOT USE THIS", scope=Scope.settings)

    # TODO: This is a quick kludge to allow CS50 (and other courses) to
    # specify their own discussion forums as external links by specifying a
    # "discussion_link" in their policy JSON file. This should later get
    # folded in with Syllabus, Course Info, and additional Custom tabs in a
    # more sensible framework later.
    discussion_link = String(help="DO NOT USE THIS", scope=Scope.settings)

    # TODO: same as above, intended to let internal CS50 hide the progress tab
    # until we get grade integration set up.
    # Explicit comparison to True because we always want to return a bool.
    hide_progress_tab = Boolean(help="DO NOT USE THIS", scope=Scope.settings)

    template_dir_name = 'course'


    def __init__(self, *args, **kwargs):
        super(CourseDescriptor, self).__init__(*args, **kwargs)

        if self.wiki_slug is None:
            self.wiki_slug = self.location.course

        msg = None
        if self.start is None:
            msg = "Course loaded without a valid start date. id = %s" % self.id
            # hack it -- start in 1970
            self.start = time.gmtime(0)
            log.critical(msg)
            self.system.error_tracker(msg)

        # NOTE: relies on the modulestore to call set_grading_policy() right after
        # init.  (Modulestore is in charge of figuring out where to load the policy from)

        # NOTE (THK): This is a last-minute addition for Fall 2012 launch to dynamically
        #   disable the syllabus content for courses that do not provide a syllabus
        self.syllabus_present = self.system.resources_fs.exists(path('syllabus'))

        self.set_grading_policy(self.grading_policy)

    def defaut_grading_policy(self):
        """
        Return a dict which is a copy of the default grading policy
        """
        default = {"GRADER" : [
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
                    "weight" : 0.15
                },
                {
                    "type" : "Midterm Exam",
                    "short_label" : "Midterm",
                    "min_count" : 1,
                    "drop_count" : 0,
                    "weight" : 0.3
                },
                {
                    "type" : "Final Exam",
                    "short_label" : "Final",
                    "min_count" : 1,
                    "drop_count" : 0,
                    "weight" : 0.4
                }
            ],
            "GRADE_CUTOFFS" : {
                "Pass" : 0.5
            }}
        return copy.deepcopy(default)

    def set_grading_policy(self, course_policy):
        """
        The JSON object can have the keys GRADER and GRADE_CUTOFFS. If either is
        missing, it reverts to the default.
        """
        if course_policy is None:
            course_policy = {}

        # Load the global settings as a dictionary
        grading_policy = self.defaut_grading_policy()

        # Override any global settings with the course settings
        grading_policy.update(course_policy)

        # Here is where we should parse any configurations, so that we can fail early
        grading_policy['RAW_GRADER'] = grading_policy['GRADER']  # used for cms access
        grading_policy['GRADER'] = grader_from_conf(grading_policy['GRADER'])
        self._grading_policy = grading_policy

    @classmethod
    def read_grading_policy(cls, paths, system):
        """Load a grading policy from the specified paths, in order, if it exists."""
        # Default to a blank policy dict
        policy_str = '{}'

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
        xml_obj = etree.parse(course_file, parser=edx_xml_parser).getroot()

        policy_dir = None
        url_name = xml_obj.get('url_name', xml_obj.get('slug'))
        if url_name:
            policy_dir = 'policies/' + url_name

        # Try to load grading policy
        paths = ['grading_policy.json']
        if policy_dir:
            paths = [policy_dir + '/grading_policy.json'] + paths

        policy = json.loads(cls.read_grading_policy(paths, system))

        # cdodge: import the grading policy information that is on disk and put into the
        # descriptor 'definition' bucket as a dictionary so that it is persisted in the DB
        instance.grading_policy = policy

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

        definition, children = super(CourseDescriptor, cls).definition_from_xml(xml_object, system)

        definition['textbooks'] = textbooks
        definition['wiki_slug'] = wiki_slug

        return definition, children

    def has_ended(self):
        """
        Returns True if the current time is after the specified course end date.
        Returns False if there is no end date specified.
        """
        if self.end is None:
            return False

        return time.gmtime() > self.end

    def has_started(self):
        return time.gmtime() > self.start

    @property
    def grader(self):
        return self._grading_policy['GRADER']
    
    @property
    def raw_grader(self):
        return self._grading_policy['RAW_GRADER']
    
    @raw_grader.setter
    def raw_grader(self, value):
        # NOTE WELL: this change will not update the processed graders. If we need that, this needs to call grader_from_conf
        self._grading_policy['RAW_GRADER'] = value
        self.grading_policy['GRADER'] = value

    @property
    def grade_cutoffs(self):
        return self._grading_policy['GRADE_CUTOFFS']
    
    @grade_cutoffs.setter
    def grade_cutoffs(self, value):
        self._grading_policy['GRADE_CUTOFFS'] = value
        self.grading_policy['GRADE_CUTOFFS'] = value
    

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
                if s.lms.graded:
                    xmoduledescriptors = list(yield_descriptor_descendents(s))
                    xmoduledescriptors.append(s)

                    # The xmoduledescriptors included here are only the ones that have scores.
                    section_description = { 'section_descriptor' : s, 'xmoduledescriptors' : filter(lambda child: child.has_score, xmoduledescriptors) }

                    section_format = s.lms.format
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
        return time.strftime("%b %d, %Y", self.advertised_start or self.start)

    @property
    def end_date_text(self):
        return time.strftime("%b %d, %Y", self.end)




    @property
    def forum_posts_allowed(self):
        try:
            blackout_periods = [(parse_time(start), parse_time(end))
                                for start, end
                                in self.discussion_blackouts]
            now = time.gmtime()
            for start, end in blackout_periods:
                if start <= now <= end:
                    return False
        except:
            log.exception("Error parsing discussion_blackouts for course {0}".format(self.id))
        
        return True

    @property
    def title(self):
        return self.display_name

    @property
    def number(self):
        return self.location.course

    @property
    def org(self):
        return self.location.org



