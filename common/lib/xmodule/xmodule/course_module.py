import logging
from cStringIO import StringIO
from math import exp
from lxml import etree
from path import path  # NOTE (THK): Only used for detecting presence of syllabus
import requests
from datetime import datetime
import dateutil.parser
from lazy import lazy

from xmodule.seq_module import SequenceDescriptor, SequenceModule
from xmodule.graders import grader_from_conf
from xmodule.tabs import CourseTabList
import json

from xblock.fields import Scope, List, String, Dict, Boolean, Integer
from .fields import Date
from django.utils.timezone import UTC

log = logging.getLogger(__name__)

# Make '_' a no-op so we can scrape strings
_ = lambda text: text

DEFAULT_START_DATE = datetime(2030, 1, 1, tzinfo=UTC())

class StringOrDate(Date):
    def from_json(self, value):
        """
        Parse an optional metadata key containing a time or a string:
        if present, assume it's a string if it doesn't parse.
        """
        try:
            result = super(StringOrDate, self).from_json(value)
        except ValueError:
            return value
        if result is None:
            return value
        else:
            return result

    def to_json(self, value):
        """
        Convert a time struct or string to a string.
        """
        try:
            result = super(StringOrDate, self).to_json(value)
        except:
            return value
        if result is None:
            return value
        else:
            return result


edx_xml_parser = etree.XMLParser(dtd_validation=False, load_dtd=False,
                                 remove_comments=True, remove_blank_text=True)

_cached_toc = {}


class Textbook(object):
    def __init__(self, title, book_url):
        self.title = title
        self.book_url = book_url

    @lazy
    def start_page(self):
        return int(self.table_of_contents[0].attrib['page'])

    @lazy
    def end_page(self):
        # The last page should be the last element in the table of contents,
        # but it may be nested. So recurse all the way down the last element
        last_el = self.table_of_contents[-1]
        while last_el.getchildren():
            last_el = last_el[-1]

        return int(last_el.attrib['page'])

    @lazy
    def table_of_contents(self):
        """
        Accesses the textbook's table of contents (default name "toc.xml") at the URL self.book_url

        Returns XML tree representation of the table of contents
        """
        toc_url = self.book_url + 'toc.xml'

        # cdodge: I've added this caching of TOC because in Mongo-backed instances (but not Filesystem stores)
        # course modules have a very short lifespan and are constantly being created and torn down.
        # Since this module in the __init__() method does a synchronous call to AWS to get the TOC
        # this is causing a big performance problem. So let's be a bit smarter about this and cache
        # each fetch and store in-mem for 10 minutes.
        # NOTE: I have to get this onto sandbox ASAP as we're having runtime failures. I'd like to swing back and
        # rewrite to use the traditional Django in-memory cache.
        try:
            # see if we already fetched this
            if toc_url in _cached_toc:
                (table_of_contents, timestamp) = _cached_toc[toc_url]
                age = datetime.now(UTC) - timestamp
                # expire every 10 minutes
                if age.seconds < 600:
                    return table_of_contents
        except Exception as err:
            pass

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

    def __eq__(self, other):
        return (self.title == other.title and
                self.book_url == other.book_url)

    def __ne__(self, other):
        return not self == other


class TextbookList(List):
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
                json_data.append((val.title, val.book_url))
            elif isinstance(val, tuple):
                json_data.append(val)
            else:
                continue
        return json_data


class CourseFields(object):
    lti_passports = List(
        display_name=_("LTI Passports"),
        help=_("Enter the passports for course LTI tools in the following format: \"id\":\"client_key:client_secret\"."),
        scope=Scope.settings
    )
    textbooks = TextbookList(help="List of pairs of (title, url) for textbooks used in this course",
                             default=[], scope=Scope.content)

    wiki_slug = String(help="Slug that points to the wiki for this course", scope=Scope.content)
    enrollment_start = Date(help="Date that enrollment for this class is opened", scope=Scope.settings)
    enrollment_end = Date(help="Date that enrollment for this class is closed", scope=Scope.settings)
    start = Date(help="Start time when this module is visible",
                 default=DEFAULT_START_DATE,
                 scope=Scope.settings)
    end = Date(help="Date that this class ends", scope=Scope.settings)
    advertised_start = String(
        display_name=_("Course Advertised Start Date"),
        help=_("Enter the date you want to advertise as the course start date, if this date is different from the set start date. To advertise the set start date, enter null."),
        scope=Scope.settings
    )
    grading_policy = Dict(help="Grading policy definition for this class",
                          default={"GRADER": [
                              {
                                  "type": "Homework",
                                  "min_count": 12,
                                  "drop_count": 2,
                                  "short_label": "HW",
                                  "weight": 0.15
                              },
                              {
                                  "type": "Lab",
                                  "min_count": 12,
                                  "drop_count": 2,
                                  "weight": 0.15
                              },
                              {
                                  "type": "Midterm Exam",
                                  "short_label": "Midterm",
                                  "min_count": 1,
                                  "drop_count": 0,
                                  "weight": 0.3
                              },
                              {
                                  "type": "Final Exam",
                                  "short_label": "Final",
                                  "min_count": 1,
                                  "drop_count": 0,
                                  "weight": 0.4
                              }
                          ],
                              "GRADE_CUTOFFS": {
                                  "Pass": 0.5
                              }},
                          scope=Scope.content)
    show_calculator = Boolean(
        display_name=_("Show Calculator"),
        help=_("Enter true or false. When true, students can see the calculator in the course."),
        default=False,
        scope=Scope.settings
    )
    display_name = String(
        help=_("Enter the name of the course as it should appear in the edX.org course list."),
        default="Empty",
        display_name=_("Course Display Name"),
        scope=Scope.settings
    )
    course_edit_method = String(
        display_name=_("Course Editor"),
        help=_("Enter the method by which this course is edited (\"XML\" or \"Studio\")."),
        default="Studio",
        scope=Scope.settings,
        deprecated=True  # Deprecated because someone would not edit this value within Studio.
    )
    show_chat = Boolean(
        display_name=_("Show Chat Widget"),
        help=_("Enter true or false. When true, students can see the chat widget in the course."),
        default=False,
        scope=Scope.settings
    )
    tabs = CourseTabList(help="List of tabs to enable in this course", scope=Scope.settings, default=[])
    end_of_course_survey_url = String(
        display_name=_("Course Survey URL"),
        help=_("Enter the URL for the end-of-course survey. If your course does not have a survey, enter null."),
        scope=Scope.settings
    )
    discussion_blackouts = List(
        display_name=_("Discussion Blackout Dates"),
        help=_("Enter pairs of dates between which students cannot post to discussion forums, formatted as \"YYYY-MM-DD-YYYY-MM-DD\". To specify times as well as dates, format the pairs as \"YYYY-MM-DDTHH:MM-YYYY-MM-DDTHH:MM\" (be sure to include the \"T\" between the date and time)."),
        scope=Scope.settings
    )
    discussion_topics = Dict(
        display_name=_("Discussion Topic Mapping"),
        help=_("Enter discussion categories in the following format: \"CategoryName\": {\"id\": \"i4x-InstitutionName-CourseNumber-course-CourseRun\"}. For example, one discussion category may be \"Lydian Mode\": {\"id\": \"i4x-UniversityX-MUS101-course-2014_T1\"}."),
        scope=Scope.settings
    )
    discussion_sort_alpha = Boolean(
        display_name=_("Discussion Sorting Alphabetical"),
        scope=Scope.settings, default=False,
        help=_("Enter true or false. If true, discussion categories and subcategories are sorted alphabetically. If false, they are sorted chronologically.")
    )
    announcement = Date(
        display_name=_("Course Announcement Date"),
        help=_("Enter the date to announce your course."),
        scope=Scope.settings
    )
    cohort_config = Dict(
        display_name=_("Cohort Configuration"),
        help=_("Cohorts are not currently supported by edX."),
        scope=Scope.settings
    )
    is_new = Boolean(
        display_name=_("Course Is New"),
        help=_("Enter true or false. If true, the course appears in the list of new courses on edx.org, and a New! badge temporarily appears next to the course image."),
        scope=Scope.settings
    )
    no_grade = Boolean(
        display_name=_("Course Not Graded"),
        help=_("Enter true or false. If true, the course will not be graded."),
        default=False,
        scope=Scope.settings
    )
    disable_progress_graph = Boolean(
        display_name=_("Disable Progress Graph"),
        help=_("Enter true or false. If true, students cannot view the progress graph."),
        default=False,
        scope=Scope.settings
    )
    pdf_textbooks = List(
        display_name=_("PDF Textbooks"),
        help=_("List of dictionaries containing pdf_textbook configuration"), scope=Scope.settings
    )
    html_textbooks = List(
        display_name=_("HTML Textbooks"),
        help=_("For HTML textbooks that appear as separate tabs in the courseware, enter the name of the tab (usually the name of the book) as well as the URLs and titles of all the chapters in the book."),
        scope=Scope.settings
    )
    remote_gradebook = Dict(
        display_name=_("Remote Gradebook"),
        help=_("Enter the remote gradebook mapping. Only use this setting when REMOTE_GRADEBOOK_URL has been specified."),
        scope=Scope.settings
    )
    allow_anonymous = Boolean(
        display_name=_("Allow Anonymous Discussion Posts"),
        help=_("Enter true or false. If true, students can create discussion posts that are anonymous to all users."),
        scope=Scope.settings, default=True
    )
    allow_anonymous_to_peers = Boolean(
        display_name=_("Allow Anonymous Discussion Posts to Peers"),
        help=_("Enter true or false. If true, students can create discussion posts that are anonymous to other students. This setting does not make posts anonymous to course staff."),
        scope=Scope.settings, default=False
    )
    advanced_modules = List(
        display_name=_("Advanced Module List"),
        help=_("Enter the names of the advanced components to use in your course."),
        scope=Scope.settings
    )
    has_children = True
    checklists = List(scope=Scope.settings,
                      default=[
                          {"short_description": _("Getting Started With Studio"),
                           "items": [{"short_description": _("Add Course Team Members"),
                                      "long_description": _("Grant your collaborators permission to edit your course so you can work together."),
                                      "is_checked": False,
                                      "action_url": "ManageUsers",
                                      "action_text": _("Edit Course Team"),
                                      "action_external": False},
                                     {"short_description": _("Set Important Dates for Your Course"),
                                      "long_description": _("Establish your course's student enrollment and launch dates on the Schedule and Details page."),
                                      "is_checked": False,
                                      "action_url": "SettingsDetails",
                                      "action_text": _("Edit Course Details &amp; Schedule"),
                                      "action_external": False},
                                     {"short_description": _("Draft Your Course's Grading Policy"),
                                      "long_description": _("Set up your assignment types and grading policy even if you haven't created all your assignments."),
                                      "is_checked": False,
                                      "action_url": "SettingsGrading",
                                      "action_text": _("Edit Grading Settings"),
                                      "action_external": False},
                                     {"short_description": _("Explore the Other Studio Checklists"),
                                      "long_description": _("Discover other available course authoring tools, and find help when you need it."),
                                      "is_checked": False,
                                      "action_url": "",
                                      "action_text": "",
                                      "action_external": False}]},
                          {"short_description": _("Draft a Rough Course Outline"),
                           "items": [{"short_description": _("Create Your First Section and Subsection"),
                                      "long_description": _("Use your course outline to build your first Section and Subsection."),
                                      "is_checked": False,
                                      "action_url": "CourseOutline",
                                      "action_text": _("Edit Course Outline"),
                                      "action_external": False},
                                     {"short_description": _("Set Section Release Dates"),
                                      "long_description": _("Specify the release dates for each Section in your course. Sections become visible to students on their release dates."),
                                      "is_checked": False,
                                      "action_url": "CourseOutline",
                                      "action_text": _("Edit Course Outline"),
                                      "action_external": False},
                                     {"short_description": _("Designate a Subsection as Graded"),
                                      "long_description": _("Set a Subsection to be graded as a specific assignment type. Assignments within graded Subsections count toward a student's final grade."),
                                      "is_checked": False,
                                      "action_url": "CourseOutline",
                                      "action_text": _("Edit Course Outline"),
                                      "action_external": False},
                                     {"short_description": _("Reordering Course Content"),
                                      "long_description": _("Use drag and drop to reorder the content in your course."),
                                      "is_checked": False,
                                      "action_url": "CourseOutline",
                                      "action_text": _("Edit Course Outline"),
                                      "action_external": False},
                                     {"short_description": _("Renaming Sections"),
                                      "long_description": _("Rename Sections by clicking the Section name from the Course Outline."),
                                      "is_checked": False,
                                      "action_url": "CourseOutline",
                                      "action_text": _("Edit Course Outline"),
                                      "action_external": False},
                                     {"short_description": _("Deleting Course Content"),
                                      "long_description": _("Delete Sections, Subsections, or Units you don't need anymore. Be careful, as there is no Undo function."),
                                      "is_checked": False,
                                      "action_url": "CourseOutline",
                                      "action_text": _("Edit Course Outline"),
                                      "action_external": False},
                                     {"short_description": _("Add an Instructor-Only Section to Your Outline"),
                                      "long_description": _("Some course authors find using a section for unsorted, in-progress work useful. To do this, create a section and set the release date to the distant future."),
                                      "is_checked": False,
                                      "action_url": "CourseOutline",
                                      "action_text": _("Edit Course Outline"),
                                      "action_external": False}]},
                          {"short_description": _("Explore edX's Support Tools"),
                           "items": [{"short_description": _("Explore the Studio Help Forum"),
                                      "long_description": _("Access the Studio Help forum from the menu that appears when you click your user name in the top right corner of Studio."),
                                      "is_checked": False,
                                      "action_url": "http://help.edge.edx.org/",
                                      "action_text": _("Visit Studio Help"),
                                      "action_external": True},
                                     {"short_description": _("Enroll in edX 101"),
                                      "long_description": _("Register for edX 101, edX's primer for course creation."),
                                      "is_checked": False,
                                      "action_url": "https://edge.edx.org/courses/edX/edX101/How_to_Create_an_edX_Course/about",
                                      "action_text": _("Register for edX 101"),
                                      "action_external": True},
                                     {"short_description": _("Download the Studio Documentation"),
                                      "long_description": _("Download the searchable Studio reference documentation in PDF form."),
                                      "is_checked": False,
                                      "action_url": "http://files.edx.org/Getting_Started_with_Studio.pdf",
                                      "action_text": _("Download Documentation"),
                                      "action_external": True}]},
                          {"short_description": _("Draft Your Course About Page"),
                           "items": [{"short_description": _("Draft a Course Description"),
                                      "long_description": _("Courses on edX have an About page that includes a course video, description, and more. Draft the text students will read before deciding to enroll in your course."),
                                      "is_checked": False,
                                      "action_url": "SettingsDetails",
                                      "action_text": _("Edit Course Schedule &amp; Details"),
                                      "action_external": False},
                                     {"short_description": _("Add Staff Bios"),
                                      "long_description": _("Showing prospective students who their instructor will be is helpful. Include staff bios on the course About page."),
                                      "is_checked": False,
                                      "action_url": "SettingsDetails",
                                      "action_text": _("Edit Course Schedule &amp; Details"),
                                      "action_external": False},
                                     {"short_description": _("Add Course FAQs"),
                                      "long_description": _("Include a short list of frequently asked questions about your course."),
                                      "is_checked": False,
                                      "action_url": "SettingsDetails",
                                      "action_text": _("Edit Course Schedule &amp; Details"),
                                      "action_external": False},
                                     {"short_description": _("Add Course Prerequisites"),
                                      "long_description": _("Let students know what knowledge and/or skills they should have before they enroll in your course."),
                                      "is_checked": False,
                                      "action_url": "SettingsDetails",
                                      "action_text": _("Edit Course Schedule &amp; Details"),
                                      "action_external": False}]}
        ])
    info_sidebar_name = String(
        display_name=_("Course Info Sidebar Name"),
        help=_("Enter the heading that you want students to see above your course handouts on the Course Info page. Your course handouts appear in the right panel of the page."),
        scope=Scope.settings, default='Course Handouts')
    show_timezone = Boolean(
        help="True if timezones should be shown on dates in the courseware. Deprecated in favor of due_date_display_format.",
        scope=Scope.settings, default=True
    )
    due_date_display_format = String(
        display_name=_("Due Date Display Format"),
        help=_("Enter the format due dates are displayed in. Due dates must be in MM-DD-YYYY, DD-MM-YYYY, YYYY-MM-DD, or YYYY-DD-MM format."),
        scope=Scope.settings, default=None
    )
    enrollment_domain = String(
        display_name=_("External Login Domain"),
        help=_("Enter the external login method students can use for the course."),
        scope=Scope.settings
    )
    certificates_show_before_end = Boolean(
        display_name=_("Certificates Downloadable Before End"),
        help=_("Enter true or false. If true, students can download certificates before the course ends, if they've met certificate requirements."),
        scope=Scope.settings,
        default=False,
        deprecated=True
    )

    certificates_display_behavior = String(
        display_name=_("Certificates Display Behavior"),
        help=_("Has three possible states: 'end', 'early_with_info', 'early_no_info'. 'end' is the default behavior, where certificates will only appear after a course has ended. 'early_with_info' will display all certificate information before a course has ended. 'early_no_info' will hide all certificate information unless a student has earned a certificate."),
        scope=Scope.settings,
        default="end"
    )
    course_image = String(
        display_name=_("Course About Page Image"),
        help=_("Edit the name of the course image file. You must upload this file on the Files & Uploads page. You can also set the course image on the Settings & Details page."),
        scope=Scope.settings,
        # Ensure that courses imported from XML keep their image
        default="images_course_image.jpg"
    )

    ## Course level Certificate Name overrides.
    cert_name_short = String(
        help=_("Between quotation marks, enter the short name of the course to use on the certificate that students receive when they complete the course."),
        display_name=_("Certificate Name (Short)"),
        scope=Scope.settings,
        default=""
    )
    cert_name_long = String(
        help=_("Between quotation marks, enter the long name of the course to use on the certificate that students receive when they complete the course."),
        display_name=_("Certificate Name (Long)"),
        scope=Scope.settings,
        default=""
    )

    # An extra property is used rather than the wiki_slug/number because
    # there are courses that change the number for different runs. This allows
    # courses to share the same css_class across runs even if they have
    # different numbers.
    #
    # TODO get rid of this as soon as possible or potentially build in a robust
    # way to add in course-specific styling. There needs to be a discussion
    # about the right way to do this, but arjun will address this ASAP. Also
    # note that the courseware template needs to change when this is removed.
    css_class = String(
        display_name=_("CSS Class for Course Reruns"),
        help=_("Allows courses to share the same css class across runs even if they have different numbers."),
        scope=Scope.settings, default="",
        deprecated=True
    )

    # TODO: This is a quick kludge to allow CS50 (and other courses) to
    # specify their own discussion forums as external links by specifying a
    # "discussion_link" in their policy JSON file. This should later get
    # folded in with Syllabus, Course Info, and additional Custom tabs in a
    # more sensible framework later.
    discussion_link = String(
        display_name=_("Discussion Forum External Link"),
        help=_("Allows specification of an external link to replace discussion forums."),
        scope=Scope.settings,
        deprecated=True
    )

    # TODO: same as above, intended to let internal CS50 hide the progress tab
    # until we get grade integration set up.
    # Explicit comparison to True because we always want to return a bool.
    hide_progress_tab = Boolean(
        display_name=_("Hide Progress Tab"),
        help=_("Allows hiding of the progress tab."),
        scope=Scope.settings,
        deprecated=True
    )

    display_organization = String(
        display_name=_("Course Organization Display String"),
        help=_("Enter the course organization that you want to appear in the courseware. This setting overrides the organization that you entered when you created the course. To use the organization that you entered when you created the course, enter null."),
        scope=Scope.settings
    )

    display_coursenumber = String(
        display_name=_("Course Number Display String"),
        help=_("Enter the course number that you want to appear in the courseware. This setting overrides the course number that you entered when you created the course. To use the course number that you entered when you created the course, enter null."),
        scope=Scope.settings
    )

    max_student_enrollments_allowed = Integer(
        display_name=_("Course Maximum Student Enrollment"),
        help=_("Enter the maximum number of students that can enroll in the course. To allow an unlimited number of students, enter null."),
        scope=Scope.settings
    )

    allow_public_wiki_access = Boolean(display_name=_("Allow Public Wiki Access"),
                                       help=_("Enter true or false. If true, edX users can view the course wiki even if they're not enrolled in the course."),
                                       default=False,
                                       scope=Scope.settings)

    invitation_only = Boolean(display_name=_("Invitation Only"),
                              help="Whether to restrict enrollment to invitation by the course staff.",
                              default=False,
                              scope=Scope.settings)

class CourseDescriptor(CourseFields, SequenceDescriptor):
    module_class = SequenceModule

    def __init__(self, *args, **kwargs):
        """
        Expects the same arguments as XModuleDescriptor.__init__
        """
        super(CourseDescriptor, self).__init__(*args, **kwargs)
        _ = self.runtime.service(self, "i18n").ugettext

        if self.wiki_slug is None:
            self.wiki_slug = self.location.course

        if self.due_date_display_format is None and self.show_timezone is False:
            # For existing courses with show_timezone set to False (and no due_date_display_format specified),
            # set the due_date_display_format to what would have been shown previously (with no timezone).
            # Then remove show_timezone so that if the user clears out the due_date_display_format,
            # they get the default date display.
            self.due_date_display_format = "DATE_TIME"
            delattr(self, 'show_timezone')

        # NOTE: relies on the modulestore to call set_grading_policy() right after
        # init.  (Modulestore is in charge of figuring out where to load the policy from)

        # NOTE (THK): This is a last-minute addition for Fall 2012 launch to dynamically
        #   disable the syllabus content for courses that do not provide a syllabus
        if self.system.resources_fs is None:
            self.syllabus_present = False
        else:
            self.syllabus_present = self.system.resources_fs.exists(path('syllabus'))

        self._grading_policy = {}
        self.set_grading_policy(self.grading_policy)

        if self.discussion_topics == {}:
            self.discussion_topics = {_('General'): {'id': self.location.html_id()}}

        if not getattr(self, "tabs", []):
            CourseTabList.initialize_default(self)

    def set_grading_policy(self, course_policy):
        """
        The JSON object can have the keys GRADER and GRADE_CUTOFFS. If either is
        missing, it reverts to the default.
        """
        if course_policy is None:
            course_policy = {}

        # Load the global settings as a dictionary
        grading_policy = self.grading_policy
        # BOY DO I HATE THIS grading_policy CODE ACROBATICS YET HERE I ADD MORE (dhm)--this fixes things persisted w/
        # defective grading policy values (but not None)
        if 'GRADER' not in grading_policy:
            grading_policy['GRADER'] = CourseFields.grading_policy.default['GRADER']
        if 'GRADE_CUTOFFS' not in grading_policy:
            grading_policy['GRADE_CUTOFFS'] = CourseFields.grading_policy.default['GRADE_CUTOFFS']

        # Override any global settings with the course settings
        grading_policy.update(course_policy)

        # Here is where we should parse any configurations, so that we can fail early
        # Use setters so that side effecting to .definitions works
        self.raw_grader = grading_policy['GRADER']  # used for cms access
        self.grade_cutoffs = grading_policy['GRADE_CUTOFFS']

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
    def from_xml(cls, xml_data, system, id_generator):
        instance = super(CourseDescriptor, cls).from_xml(xml_data, system, id_generator)

        # bleh, have to parse the XML here to just pull out the url_name attribute
        # I don't think it's stored anywhere in the instance.
        course_file = StringIO(xml_data.encode('ascii', 'ignore'))
        xml_obj = etree.parse(course_file, parser=edx_xml_parser).getroot()

        policy_dir = None
        url_name = xml_obj.get('url_name', xml_obj.get('slug'))
        if url_name:
            policy_dir = 'policies/' + url_name

        # Try to load grading policy
        paths = ['grading_policy.json']
        if policy_dir:
            paths = [policy_dir + '/grading_policy.json'] + paths

        try:
            policy = json.loads(cls.read_grading_policy(paths, system))
        except ValueError:
            system.error_tracker("Unable to decode grading policy as json")
            policy = {}

        # now set the current instance. set_grading_policy() will apply some inheritance rules
        instance.set_grading_policy(policy)

        return instance

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        textbooks = []
        for textbook in xml_object.findall("textbook"):
            textbooks.append((textbook.get('title'), textbook.get('book_url')))
            xml_object.remove(textbook)

        # Load the wiki tag if it exists
        wiki_slug = None
        wiki_tag = xml_object.find("wiki")
        if wiki_tag is not None:
            wiki_slug = wiki_tag.attrib.get("slug", default=None)
            xml_object.remove(wiki_tag)

        definition, children = super(CourseDescriptor, cls).definition_from_xml(xml_object, system)

        definition['textbooks'] = textbooks
        definition['wiki_slug'] = wiki_slug

        return definition, children

    def definition_to_xml(self, resource_fs):
        xml_object = super(CourseDescriptor, self).definition_to_xml(resource_fs)

        if len(self.textbooks) > 0:
            textbook_xml_object = etree.Element('textbook')
            for textbook in self.textbooks:
                textbook_xml_object.set('title', textbook.title)
                textbook_xml_object.set('book_url', textbook.book_url)

            xml_object.append(textbook_xml_object)

        if self.wiki_slug is not None:
            wiki_xml_object = etree.Element('wiki')
            wiki_xml_object.set('slug', self.wiki_slug)
            xml_object.append(wiki_xml_object)

        return xml_object

    def has_ended(self):
        """
        Returns True if the current time is after the specified course end date.
        Returns False if there is no end date specified.
        """
        if self.end is None:
            return False

        return datetime.now(UTC()) > self.end

    def may_certify(self):
        """
        Return True if it is acceptable to show the student a certificate download link
        """
        show_early = self.certificates_display_behavior in ('early_with_info', 'early_no_info') or self.certificates_show_before_end
        return show_early or self.has_ended()

    def has_started(self):
        return datetime.now(UTC()) > self.start

    @property
    def grader(self):
        return grader_from_conf(self.raw_grader)

    @property
    def raw_grader(self):
        # force the caching of the xblock value so that it can detect the change
        # pylint: disable=pointless-statement
        self.grading_policy['GRADER']
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

        # XBlock fields don't update after mutation
        policy = self.grading_policy
        policy['GRADE_CUTOFFS'] = value
        self.grading_policy = policy

    @property
    def lowest_passing_grade(self):
        return min(self._grading_policy['GRADE_CUTOFFS'].values())

    @property
    def is_cohorted(self):
        """
        Return whether the course is cohorted.
        """
        config = self.cohort_config
        if config is None:
            return False

        return bool(config.get("cohorted"))

    @property
    def auto_cohort(self):
        """
        Return whether the course is auto-cohorted.
        """
        if not self.is_cohorted:
            return False

        return bool(self.cohort_config.get(
            "auto_cohort", False))

    @property
    def auto_cohort_groups(self):
        """
        Return the list of groups to put students into.  Returns [] if not
        specified. Returns specified list even if is_cohorted and/or auto_cohort are
        false.
        """
        if self.cohort_config is None:
            return []
        else:
            return self.cohort_config.get("auto_cohort_groups", [])

    @property
    def top_level_discussion_topic_ids(self):
        """
        Return list of topic ids defined in course policy.
        """
        topics = self.discussion_topics
        return [d["id"] for d in topics.values()]

    @property
    def cohorted_discussions(self):
        """
        Return the set of discussions that is explicitly cohorted.  It may be
        the empty set.  Note that all inline discussions are automatically
        cohorted based on the course's is_cohorted setting.
        """
        config = self.cohort_config
        if config is None:
            return set()

        return set(config.get("cohorted_discussions", []))

    @property
    def is_newish(self):
        """
        Returns if the course has been flagged as new. If
        there is no flag, return a heuristic value considering the
        announcement and the start dates.
        """
        flag = self.is_new
        if flag is None:
            # Use a heuristic if the course has not been flagged
            announcement, start, now = self._sorting_dates()
            if announcement and (now - announcement).days < 30:
                # The course has been announced for less that month
                return True
            elif (now - start).days < 1:
                # The course has not started yet
                return True
            else:
                return False
        elif isinstance(flag, basestring):
            return flag.lower() in ['true', 'yes', 'y']
        else:
            return bool(flag)

    @property
    def sorting_score(self):
        """
        Returns a tuple that can be used to sort the courses according
        the how "new" they are. The "newness" score is computed using a
        heuristic that takes into account the announcement and
        (advertized) start dates of the course if available.

        The lower the number the "newer" the course.
        """
        # Make courses that have an announcement date shave a lower
        # score than courses than don't, older courses should have a
        # higher score.
        announcement, start, now = self._sorting_dates()
        scale = 300.0  # about a year
        if announcement:
            days = (now - announcement).days
            score = -exp(-days / scale)
        else:
            days = (now - start).days
            score = exp(days / scale)
        return score

    def _sorting_dates(self):
        # utility function to get datetime objects for dates used to
        # compute the is_new flag and the sorting_score

        announcement = self.announcement
        if announcement is not None:
            announcement = announcement

        try:
            start = dateutil.parser.parse(self.advertised_start)
            if start.tzinfo is None:
                start = start.replace(tzinfo=UTC())
        except (ValueError, AttributeError):
            start = self.start

        now = datetime.now(UTC())

        return announcement, start, now

    @lazy
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
            all the xmodule state for a FieldDataCache without walking
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
            for s in c.get_children():
                if s.graded:
                    xmoduledescriptors = list(yield_descriptor_descendents(s))
                    xmoduledescriptors.append(s)

                    # The xmoduledescriptors included here are only the ones that have scores.
                    section_description = {
                        'section_descriptor': s,
                        'xmoduledescriptors': filter(lambda child: child.has_score, xmoduledescriptors)
                    }

                    section_format = s.format if s.format is not None else ''
                    graded_sections[section_format] = graded_sections.get(section_format, []) + [section_description]

                    all_descriptors.extend(xmoduledescriptors)
                    all_descriptors.append(s)

        return {'graded_sections': graded_sections,
                'all_descriptors': all_descriptors, }

    @staticmethod
    def make_id(org, course, url_name):
        return '/'.join([org, course, url_name])

    @property
    def id(self):
        """Return the course_id for this course"""
        return self.location.course_key

    @property
    def start_date_text(self):
        """
        Returns the desired text corresponding the course's start date.  Prefers .advertised_start,
        then falls back to .start
        """
        i18n = self.runtime.service(self, "i18n")
        _ = i18n.ugettext
        strftime = i18n.strftime

        def try_parse_iso_8601(text):
            try:
                result = Date().from_json(text)
                if result is None:
                    result = text.title()
                else:
                    result = strftime(result, "SHORT_DATE")
            except ValueError:
                result = text.title()

            return result

        if isinstance(self.advertised_start, basestring):
            return try_parse_iso_8601(self.advertised_start)
        elif self.start_date_is_still_default:
            # Translators: TBD stands for 'To Be Determined' and is used when a course
            # does not yet have an announced start date.
            return _('TBD')
        else:
            when = self.advertised_start or self.start
            return strftime(when, "SHORT_DATE")

    @property
    def start_date_is_still_default(self):
        """
        Checks if the start date set for the course is still default, i.e. .start has not been modified,
        and .advertised_start has not been set.
        """
        return self.advertised_start is None and self.start == CourseFields.start.default

    @property
    def end_date_text(self):
        """
        Returns the end date for the course formatted as a string.

        If the course does not have an end date set (course.end is None), an empty string will be returned.
        """
        if self.end is None:
            return ''
        else:
            strftime = self.runtime.service(self, "i18n").strftime
            return strftime(self.end, "SHORT_DATE")

    @property
    def forum_posts_allowed(self):
        date_proxy = Date()
        try:
            blackout_periods = [(date_proxy.from_json(start),
                                 date_proxy.from_json(end))
                                for start, end
                                in self.discussion_blackouts]
            now = datetime.now(UTC())
            for start, end in blackout_periods:
                if start <= now <= end:
                    return False
        except:
            log.exception("Error parsing discussion_blackouts for course {0}".format(self.id))

        return True

    @property
    def number(self):
        return self.location.course

    @property
    def display_number_with_default(self):
        """
        Return a display course number if it has been specified, otherwise return the 'course' that is in the location
        """
        if self.display_coursenumber:
            return self.display_coursenumber

        return self.number

    @property
    def org(self):
        return self.location.org

    @property
    def display_org_with_default(self):
        """
        Return a display organization if it has been specified, otherwise return the 'org' that is in the location
        """
        if self.display_organization:
            return self.display_organization

        return self.org
