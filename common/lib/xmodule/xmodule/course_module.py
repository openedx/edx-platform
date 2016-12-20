"""
Django module container for classes and operations related to the "Course Module" content type
"""
import json
import logging
from cStringIO import StringIO
from datetime import datetime

import requests
from django.utils.timezone import UTC
from lazy import lazy
from lxml import etree
from path import Path as path
from xblock.core import XBlock
from xblock.fields import Scope, List, String, Dict, Boolean, Integer, Float

from xmodule import course_metadata_utils
from xmodule.course_metadata_utils import DEFAULT_START_DATE
from xmodule.exceptions import UndefinedContext
from xmodule.graders import grader_from_conf
from xmodule.mixin import LicenseMixin
from xmodule.seq_module import SequenceDescriptor, SequenceModule
from xmodule.tabs import CourseTabList, InvalidTabsException
from .fields import Date

log = logging.getLogger(__name__)

# Make '_' a no-op so we can scrape strings. Using lambda instead of
#  `django.utils.translation.ugettext_noop` because Django cannot be imported in this file
_ = lambda text: text

CATALOG_VISIBILITY_CATALOG_AND_ABOUT = "both"
CATALOG_VISIBILITY_ABOUT = "about"
CATALOG_VISIBILITY_NONE = "none"


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
        log.info("Retrieving textbook table of contents from %s", toc_url)
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
        help=_('Enter the passports for course LTI tools in the following format: "id:client_key:client_secret".'),
        scope=Scope.settings
    )
    textbooks = TextbookList(
        help=_("List of pairs of (title, url) for textbooks used in this course"),
        default=[],
        scope=Scope.content
    )

    wiki_slug = String(help=_("Slug that points to the wiki for this course"), scope=Scope.content)
    enable_enrollment_email = Boolean(help="Whether to send notification email upon enrollment or not", default=False, scope=Scope.settings)
    enrollment_start = Date(help=_("Date that enrollment for this class is opened"), scope=Scope.settings)
    enrollment_end = Date(help=_("Date that enrollment for this class is closed"), scope=Scope.settings)
    start = Date(
        help=_("Start time when this module is visible"),
        default=DEFAULT_START_DATE,
        scope=Scope.settings
    )
    end = Date(help=_("Date that this class ends"), scope=Scope.settings)
    cosmetic_display_price = Integer(
        display_name=_("Cosmetic Course Display Price"),
        help=_(
            "The cost displayed to students for enrolling in the course. If a paid course registration price is "
            "set by an administrator in the database, that price will be displayed instead of this one."
        ),
        default=0,
        scope=Scope.settings,
    )
    advertised_start = String(
        display_name=_("Course Advertised Start Date"),
        help=_(
            "Enter the date you want to advertise as the course start date, if this date is different from the set "
            "start date. To advertise the set start date, enter null."
        ),
        scope=Scope.settings
    )
    pre_requisite_courses = List(
        display_name=_("Pre-Requisite Courses"),
        help=_("Pre-Requisite Course key if this course has a pre-requisite course"),
        scope=Scope.settings
    )
    grading_policy = Dict(
        help=_("Grading policy definition for this class"),
        default={
            "GRADER": [
                {
                    "type": "Homework",
                    "min_count": 12,
                    "drop_count": 2,
                    "short_label": "HW",
                    "weight": 0.15,
                },
                {
                    "type": "Lab",
                    "min_count": 12,
                    "drop_count": 2,
                    "weight": 0.15,
                },
                {
                    "type": "Midterm Exam",
                    "short_label": "Midterm",
                    "min_count": 1,
                    "drop_count": 0,
                    "weight": 0.3,
                },
                {
                    "type": "Final Exam",
                    "short_label": "Final",
                    "min_count": 1,
                    "drop_count": 0,
                    "weight": 0.4,
                }
            ],
            "GRADE_CUTOFFS": {
                "Pass": 0.5,
            },
        },
        scope=Scope.content
    )
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
        help=_('Enter the method by which this course is edited ("XML" or "Studio").'),
        default="Studio",
        scope=Scope.settings,
        deprecated=True  # Deprecated because someone would not edit this value within Studio.
    )
    tabs = CourseTabList(help="List of tabs to enable in this course", scope=Scope.settings, default=[])
    end_of_course_survey_url = String(
        display_name=_("Course Survey URL"),
        help=_("Enter the URL for the end-of-course survey. If your course does not have a survey, enter null."),
        scope=Scope.settings,
        deprecated=True  # We wish to remove this entirely, TNL-3399
    )
    discussion_blackouts = List(
        display_name=_("Discussion Blackout Dates"),
        help=_(
            'Enter pairs of dates between which students cannot post to discussion forums. Inside the provided '
            'brackets, enter an additional set of square brackets surrounding each pair of dates you add. '
            'Format each pair of dates as ["YYYY-MM-DD", "YYYY-MM-DD"]. To specify times as well as dates, '
            'format each pair as ["YYYY-MM-DDTHH:MM", "YYYY-MM-DDTHH:MM"]. Be sure to include the "T" between '
            'the date and time. For example, an entry defining two blackout periods looks like this, including '
            'the outer pair of square brackets: [["2015-09-15", "2015-09-21"], ["2015-10-01", "2015-10-08"]] '
        ),
        scope=Scope.settings
    )
    discussion_topics = Dict(
        display_name=_("Discussion Topic Mapping"),
        help=_(
            'Enter discussion categories in the following format: "CategoryName": '
            '{"id": "i4x-InstitutionName-CourseNumber-course-CourseRun"}. For example, one discussion '
            'category may be "Lydian Mode": {"id": "i4x-UniversityX-MUS101-course-2015_T1"}. The "id" '
            'value for each category must be unique. In "id" values, the only special characters that are '
            'supported are underscore, hyphen, and period.'
        ),
        scope=Scope.settings
    )
    discussion_sort_alpha = Boolean(
        display_name=_("Discussion Sorting Alphabetical"),
        scope=Scope.settings, default=False,
        help=_(
            "Enter true or false. If true, discussion categories and subcategories are sorted alphabetically. "
            "If false, they are sorted chronologically."
        )
    )
    announcement = Date(
        display_name=_("Course Announcement Date"),
        help=_("Enter the date to announce your course."),
        scope=Scope.settings
    )
    cohort_config = Dict(
        display_name=_("Cohort Configuration"),
        help=_(
            "Enter policy keys and values to enable the cohort feature, define automated student assignment to "
            "groups, or identify any course-wide discussion topics as private to cohort members."
        ),
        scope=Scope.settings
    )
    is_new = Boolean(
        display_name=_("Course Is New"),
        help=_(
            "Enter true or false. If true, the course appears in the list of new courses on edx.org, and a New! "
            "badge temporarily appears next to the course image."
        ),
        scope=Scope.settings
    )
    mobile_available = Boolean(
        display_name=_("Mobile Course Available"),
        help=_("Enter true or false. If true, the course will be available to mobile devices."),
        default=False,
        scope=Scope.settings
    )
    video_upload_pipeline = Dict(
        display_name=_("Video Upload Credentials"),
        help=_("Enter the unique identifier for your course's video files provided by edX."),
        scope=Scope.settings
    )
    facebook_url = String(
        help=_(
            "Enter the URL for the official course Facebook group. "
            "If you provide a URL, the mobile app includes a button that students can tap to access the group."
        ),
        default=None,
        display_name=_("Facebook URL"),
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
        help=_(
            "For HTML textbooks that appear as separate tabs in the courseware, enter the name of the tab (usually "
            "the name of the book) as well as the URLs and titles of all the chapters in the book."
        ),
        scope=Scope.settings
    )
    remote_gradebook = Dict(
        display_name=_("Remote Gradebook"),
        help=_(
            "Enter the remote gradebook mapping. Only use this setting when "
            "REMOTE_GRADEBOOK_URL has been specified."
        ),
        scope=Scope.settings
    )
    enable_ccx = Boolean(
        # Translators: Custom Courses for edX (CCX) is an edX feature for re-using course content. CCX Coach is
        # a role created by a course Instructor to enable a person (the "Coach") to manage the custom course for
        # his students.
        display_name=_("Enable CCX"),
        help=_(
            # Translators: Custom Courses for edX (CCX) is an edX feature for re-using course content. CCX Coach is
            # a role created by a course Instructor to enable a person (the "Coach") to manage the custom course for
            # his students.
            "Allow course instructors to assign CCX Coach roles, and allow coaches to manage Custom Courses on edX."
            " When false, Custom Courses cannot be created, but existing Custom Courses will be preserved."
        ),
        default=False,
        scope=Scope.settings
    )
    ccx_connector = String(
        # Translators: Custom Courses for edX (CCX) is an edX feature for re-using course content.
        display_name=_("CCX Connector URL"),
        # Translators: Custom Courses for edX (CCX) is an edX feature for re-using course content.
        help=_(
            "URL for CCX Connector application for managing creation of CCXs. (optional)."
            " Ignored unless 'Enable CCX' is set to 'true'."
        ),
        scope=Scope.settings, default=""
    )
    allow_anonymous = Boolean(
        display_name=_("Allow Anonymous Discussion Posts"),
        help=_("Enter true or false. If true, students can create discussion posts that are anonymous to all users."),
        scope=Scope.settings, default=True
    )
    allow_anonymous_to_peers = Boolean(
        display_name=_("Allow Anonymous Discussion Posts to Peers"),
        help=_(
            "Enter true or false. If true, students can create discussion posts that are anonymous to other "
            "students. This setting does not make posts anonymous to course staff."
        ),
        scope=Scope.settings, default=False
    )
    advanced_modules = List(
        display_name=_("Advanced Module List"),
        help=_("Enter the names of the advanced components to use in your course."),
        scope=Scope.settings
    )
    has_children = True
    info_sidebar_name = String(
        display_name=_("Course Home Sidebar Name"),
        help=_(
            "Enter the heading that you want students to see above your course handouts on the Course Home page. "
            "Your course handouts appear in the right panel of the page."
        ),
        scope=Scope.settings, default=_('Course Handouts'))
    show_timezone = Boolean(
        help=_(
            "True if timezones should be shown on dates in the courseware. "
            "Deprecated in favor of due_date_display_format."
        ),
        scope=Scope.settings, default=True
    )
    due_date_display_format = String(
        display_name=_("Due Date Display Format"),
        help=_(
            "Enter the format for due dates. The default is Mon DD, YYYY. Enter \"%m-%d-%Y\" for MM-DD-YYYY, "
            "\"%d-%m-%Y\" for DD-MM-YYYY, \"%Y-%m-%d\" for YYYY-MM-DD, or \"%Y-%d-%m\" for YYYY-DD-MM."
        ),
        scope=Scope.settings, default=None
    )
    enrollment_domain = String(
        display_name=_("External Login Domain"),
        help=_("Enter the external login method students can use for the course."),
        scope=Scope.settings
    )
    certificates_show_before_end = Boolean(
        display_name=_("Certificates Downloadable Before End"),
        help=_(
            "Enter true or false. If true, students can download certificates before the course ends, if they've "
            "met certificate requirements."
        ),
        scope=Scope.settings,
        default=False,
        deprecated=True
    )

    certificates_display_behavior = String(
        display_name=_("Certificates Display Behavior"),
        help=_(
            "Enter end, early_with_info, or early_no_info. After certificate generation, students who passed see a "
            "link to their certificates on the dashboard and students who did not pass see information about the "
            "grading configuration. The default is end, which displays this certificate information to all students "
            "after the course end date. To display this certificate information to all students as soon as "
            "certificates are generated, enter early_with_info. To display only the links to passing students as "
            "soon as certificates are generated, enter early_no_info."
        ),
        scope=Scope.settings,
        default="end"
    )
    course_image = String(
        display_name=_("Course About Page Image"),
        help=_(
            "Edit the name of the course image file. You must upload this file on the Files & Uploads page. "
            "You can also set the course image on the Settings & Details page."
        ),
        scope=Scope.settings,
        # Ensure that courses imported from XML keep their image
        default="images_course_image.jpg"
    )
    issue_badges = Boolean(
        display_name=_("Issue Open Badges"),
        help=_(
            "Issue Open Badges badges for this course. Badges are generated when certificates are created."
        ),
        scope=Scope.settings,
        default=True
    )
    ## Course level Certificate Name overrides.
    cert_name_short = String(
        help=_(
            'Use this setting only when generating PDF certificates. '
            'Between quotation marks, enter the short name of the type of certificate that '
            'students receive when they complete the course. For instance, "Certificate".'
        ),
        display_name=_("Certificate Name (Short)"),
        scope=Scope.settings,
        default=""
    )
    cert_name_long = String(
        help=_(
            'Use this setting only when generating PDF certificates. '
            'Between quotation marks, enter the long name of the type of certificate that students '
            'receive when they complete the course. For instance, "Certificate of Achievement".'
        ),
        display_name=_("Certificate Name (Long)"),
        scope=Scope.settings,
        default=""
    )
    cert_html_view_enabled = Boolean(
        display_name=_("Certificate Web/HTML View Enabled"),
        help=_("If true, certificate Web/HTML views are enabled for the course."),
        scope=Scope.settings,
        default=False,
    )
    cert_html_view_overrides = Dict(
        # Translators: This field is the container for course-specific certifcate configuration values
        display_name=_("Certificate Web/HTML View Overrides"),
        # Translators: These overrides allow for an alternative configuration of the certificate web view
        help=_("Enter course-specific overrides for the Web/HTML template parameters here (JSON format)"),
        scope=Scope.settings,
    )

    # Specific certificate information managed via Studio (should eventually fold other cert settings into this)
    certificates = Dict(
        # Translators: This field is the container for course-specific certifcate configuration values
        display_name=_("Certificate Configuration"),
        # Translators: These overrides allow for an alternative configuration of the certificate web view
        help=_("Enter course-specific configuration information here (JSON format)"),
        scope=Scope.settings,
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
        help=_(
            "Enter the course organization that you want to appear in the courseware. This setting overrides the "
            "organization that you entered when you created the course. To use the organization that you entered "
            "when you created the course, enter null."
        ),
        scope=Scope.settings
    )

    display_coursenumber = String(
        display_name=_("Course Number Display String"),
        help=_(
            "Enter the course number that you want to appear in the courseware. This setting overrides the course "
            "number that you entered when you created the course. To use the course number that you entered when "
            "you created the course, enter null."
        ),
        scope=Scope.settings,
        default=""
    )

    max_student_enrollments_allowed = Integer(
        display_name=_("Course Maximum Student Enrollment"),
        help=_(
            "Enter the maximum number of students that can enroll in the course. To allow an unlimited number of "
            "students, enter null."
        ),
        scope=Scope.settings
    )

    allow_public_wiki_access = Boolean(
        display_name=_("Allow Public Wiki Access"),
        help=_(
            "Enter true or false. If true, edX users can view the course wiki even "
            "if they're not enrolled in the course."
        ),
        default=False,
        scope=Scope.settings
    )

    invitation_only = Boolean(
        display_name=_("Invitation Only"),
        help=_("Whether to restrict enrollment to invitation by the course staff."),
        default=False,
        scope=Scope.settings
    )

    course_survey_name = String(
        display_name=_("Pre-Course Survey Name"),
        help=_("Name of SurveyForm to display as a pre-course survey to the user."),
        default=None,
        scope=Scope.settings,
        deprecated=True
    )

    course_survey_required = Boolean(
        display_name=_("Pre-Course Survey Required"),
        help=_(
            "Specify whether students must complete a survey before they can view your course content. If you "
            "set this value to true, you must add a name for the survey to the Course Survey Name setting above."
        ),
        default=False,
        scope=Scope.settings,
        deprecated=True
    )

    catalog_visibility = String(
        display_name=_("Course Visibility In Catalog"),
        help=_(
            "Defines the access permissions for showing the course in the course catalog. This can be set to one "
            "of three values: 'both' (show in catalog and allow access to about page), 'about' (only allow access "
            "to about page), 'none' (do not show in catalog and do not allow access to an about page)."
        ),
        default=CATALOG_VISIBILITY_CATALOG_AND_ABOUT,
        scope=Scope.settings,
        values=[
            {"display_name": _("Both"), "value": CATALOG_VISIBILITY_CATALOG_AND_ABOUT},
            {"display_name": _("About"), "value": CATALOG_VISIBILITY_ABOUT},
            {"display_name": _("None"), "value": CATALOG_VISIBILITY_NONE}]
    )

    entrance_exam_enabled = Boolean(
        display_name=_("Entrance Exam Enabled"),
        help=_(
            "Specify whether students must complete an entrance exam before they can view your course content. "
            "Note, you must enable Entrance Exams for this course setting to take effect."
        ),
        default=False,
        scope=Scope.settings,
    )

    entrance_exam_minimum_score_pct = Float(
        display_name=_("Entrance Exam Minimum Score (%)"),
        help=_(
            "Specify a minimum percentage score for an entrance exam before students can view your course content. "
            "Note, you must enable Entrance Exams for this course setting to take effect."
        ),
        default=65,
        scope=Scope.settings,
    )

    entrance_exam_id = String(
        display_name=_("Entrance Exam ID"),
        help=_("Content module identifier (location) of entrance exam."),
        default=None,
        scope=Scope.settings,
    )

    social_sharing_url = String(
        display_name=_("Social Media Sharing URL"),
        help=_(
            "If dashboard social sharing and custom course URLs are enabled, you can provide a URL "
            "(such as the URL to a course About page) that social media sites can link to. URLs must "
            "be fully qualified. For example: http://www.edx.org/course/Introduction-to-MOOCs-ITM001"
        ),
        default=None,
        scope=Scope.settings,
    )
    language = String(
        display_name=_("Course Language"),
        help=_("Specify the language of your course."),
        default=None,
        scope=Scope.settings
    )

    teams_configuration = Dict(
        display_name=_("Teams Configuration"),
        # Translators: please don't translate "id".
        help=_(
            'Specify the maximum team size and topics for teams inside the provided set of curly braces. '
            'Make sure that you enclose all of the sets of topic values within a set of square brackets, '
            'with a comma after the closing curly brace for each topic, and another comma after the '
            'closing square brackets. '
            'For example, to specify that teams should have a maximum of 5 participants and provide a list of '
            '2 topics, enter the configuration in this format: {example_format}. '
            'In "id" values, the only supported special characters are underscore, hyphen, and period.'
        ).format(
            # Put the sample JSON into a format variable so that translators
            # don't muck with it.
            example_format=(
                '{"topics": [{"name": "Topic1Name", "description": "Topic1Description", "id": "Topic1ID"}, '
                '{"name": "Topic2Name", "description": "Topic2Description", "id": "Topic2ID"}], "max_team_size": 5}'
            ),
        ),
        scope=Scope.settings,
    )

    enable_proctored_exams = Boolean(
        display_name=_("Enable Proctored Exams"),
        help=_(
            "Enter true or false. If this value is true, proctored exams are enabled in your course. "
            "Note that enabling proctored exams will also enable timed exams."
        ),
        default=False,
        scope=Scope.settings
    )

    enable_timed_exams = Boolean(
        display_name=_("Enable Timed Exams"),
        help=_(
            "Enter true or false. If this value is true, timed exams are enabled in your course."
        ),
        default=False,
        scope=Scope.settings
    )

    minimum_grade_credit = Float(
        display_name=_("Minimum Grade for Credit"),
        help=_(
            "The minimum grade that a learner must earn to receive credit in the course, "
            "as a decimal between 0.0 and 1.0. For example, for 75%, enter 0.75."
        ),
        default=0.8,
        scope=Scope.settings,
    )

    self_paced = Boolean(
        display_name=_("Self Paced"),
        help=_(
            "Set this to \"true\" to mark this course as self-paced. Self-paced courses do not have "
            "due dates for assignments, and students can progress through the course at any rate before "
            "the course ends."
        ),
        default=False,
        scope=Scope.settings
    )

    enable_subsection_gating = Boolean(
        display_name=_("Enable Subsection Prerequisites"),
        help=_(
            "Enter true or false. If this value is true, you can hide a "
            "subsection until learners earn a minimum score in another, "
            "prerequisite subsection."
        ),
        default=False,
        scope=Scope.settings
    )


class CourseModule(CourseFields, SequenceModule):  # pylint: disable=abstract-method
    """
    The CourseDescriptor needs its module_class to be a SequenceModule, but some code that
    expects a CourseDescriptor to have all its fields can fail if it gets a SequenceModule instead.
    This class is to make sure that all the fields are present in all cases.
    """


class CourseDescriptor(CourseFields, SequenceDescriptor, LicenseMixin):
    """
    The descriptor for the course XModule
    """
    module_class = CourseModule

    def __init__(self, *args, **kwargs):
        """
        Expects the same arguments as XModuleDescriptor.__init__
        """
        super(CourseDescriptor, self).__init__(*args, **kwargs)
        _ = self.runtime.service(self, "i18n").ugettext

        self._gating_prerequisites = None

        if self.wiki_slug is None:
            self.wiki_slug = self.location.course

        if self.due_date_display_format is None and self.show_timezone is False:
            # For existing courses with show_timezone set to False (and no due_date_display_format specified),
            # set the due_date_display_format to what would have been shown previously (with no timezone).
            # Then remove show_timezone so that if the user clears out the due_date_display_format,
            # they get the default date display.
            self.due_date_display_format = "DATE_TIME"
            del self.show_timezone

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

        try:
            if not getattr(self, "tabs", []):
                CourseTabList.initialize_default(self)
        except InvalidTabsException as err:
            raise type(err)('{msg} For course: {course_id}'.format(msg=err.message, course_id=unicode(self.id)))

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
            except IOError:
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

        # load license if it exists
        definition = LicenseMixin.parse_license_from_xml(definition, xml_object)

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

        # handle license specifically. Default the course to have a license
        # of "All Rights Reserved", if a license is not explicitly set.
        self.add_license_to_xml(xml_object, default="all-rights-reserved")

        return xml_object

    def has_ended(self):
        """
        Returns True if the current time is after the specified course end date.
        Returns False if there is no end date specified.
        """
        return course_metadata_utils.has_course_ended(self.end)

    def may_certify(self):
        """
        Return whether it is acceptable to show the student a certificate download link.
        """
        return course_metadata_utils.may_certify_for_course(
            self.certificates_display_behavior,
            self.certificates_show_before_end,
            self.has_ended()
        )

    def has_started(self):
        return course_metadata_utils.has_course_started(self.start)

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

        Note: No longer used. See openedx.core.djangoapps.course_groups.models.CourseCohortSettings.
        """
        config = self.cohort_config
        if config is None:
            return False

        return bool(config.get("cohorted"))

    @property
    def auto_cohort(self):
        """
        Return whether the course is auto-cohorted.

        Note: No longer used. See openedx.core.djangoapps.course_groups.models.CourseCohortSettings.
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

        Note: No longer used. See openedx.core.djangoapps.course_groups.models.CourseCohortSettings.
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

        Note: No longer used. See openedx.core.djangoapps.course_groups.models.CourseCohortSettings.
        """
        config = self.cohort_config
        if config is None:
            return set()

        return set(config.get("cohorted_discussions", []))

    @property
    def always_cohort_inline_discussions(self):
        """
        This allow to change the default behavior of inline discussions cohorting. By
        setting this to False, all inline discussions are non-cohorted unless their
        ids are specified in cohorted_discussions.

        Note: No longer used. See openedx.core.djangoapps.course_groups.models.CourseCohortSettings.
        """
        config = self.cohort_config
        if config is None:
            return True

        return bool(config.get("always_cohort_inline_discussions", True))

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
            announcement, start, now = course_metadata_utils.sorting_dates(
                self.start, self.advertised_start, self.announcement
            )
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
        (advertised) start dates of the course if available.

        The lower the number the "newer" the course.
        """
        return course_metadata_utils.sorting_score(self.start, self.advertised_start, self.announcement)

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
        # If this descriptor has been bound to a student, return the corresponding
        # XModule. If not, just use the descriptor itself
        try:
            module = getattr(self, '_xmodule', None)
            if not module:
                module = self
        except UndefinedContext:
            module = self

        def possibly_scored(usage_key):
            """Can this XBlock type can have a score or children?"""
            return usage_key.block_type in self.block_types_affecting_grading

        all_descriptors = []
        graded_sections = {}

        def yield_descriptor_descendents(module_descriptor):
            for child in module_descriptor.get_children(usage_key_filter=possibly_scored):
                yield child
                for module_descriptor in yield_descriptor_descendents(child):
                    yield module_descriptor

        for chapter in self.get_children():
            for section in chapter.get_children():
                if section.graded:
                    xmoduledescriptors = list(yield_descriptor_descendents(section))
                    xmoduledescriptors.append(section)

                    # The xmoduledescriptors included here are only the ones that have scores.
                    section_description = {
                        'section_descriptor': section,
                        'xmoduledescriptors': [child for child in xmoduledescriptors if child.has_score]
                    }

                    section_format = section.format if section.format is not None else ''
                    graded_sections[section_format] = graded_sections.get(section_format, []) + [section_description]

                    all_descriptors.extend(xmoduledescriptors)
                    all_descriptors.append(section)

        return {'graded_sections': graded_sections,
                'all_descriptors': all_descriptors, }

    @lazy
    def block_types_affecting_grading(self):
        """Return all block types that could impact grading (i.e. scored, or having children)."""
        return frozenset(
            cat for (cat, xblock_class) in XBlock.load_classes() if (
                getattr(xblock_class, 'has_score', False) or getattr(xblock_class, 'has_children', False)
            )
        )

    @staticmethod
    def make_id(org, course, url_name):
        return '/'.join([org, course, url_name])

    @property
    def id(self):
        """Return the course_id for this course"""
        return self.location.course_key

    def start_datetime_text(self, format_string="SHORT_DATE"):
        """
        Returns the desired text corresponding the course's start date and time in UTC.  Prefers .advertised_start,
        then falls back to .start
        """
        i18n = self.runtime.service(self, "i18n")
        return course_metadata_utils.course_start_datetime_text(
            self.start,
            self.advertised_start,
            format_string,
            i18n.ugettext,
            i18n.strftime
        )

    @property
    def start_date_is_still_default(self):
        """
        Checks if the start date set for the course is still default, i.e. .start has not been modified,
        and .advertised_start has not been set.
        """
        return course_metadata_utils.course_start_date_is_default(
            self.start,
            self.advertised_start
        )

    def end_datetime_text(self, format_string="SHORT_DATE"):
        """
        Returns the end date or date_time for the course formatted as a string.
        """
        return course_metadata_utils.course_end_datetime_text(
            self.end,
            format_string,
            self.runtime.service(self, "i18n").strftime
        )

    def get_discussion_blackout_datetimes(self):
        """
        Get a list of dicts with start and end fields with datetime values from
        the discussion_blackouts setting
        """
        date_proxy = Date()
        try:
            ret = [
                {"start": date_proxy.from_json(start), "end": date_proxy.from_json(end)}
                for start, end
                in filter(None, self.discussion_blackouts)
            ]
            for blackout in ret:
                if not blackout["start"] or not blackout["end"]:
                    raise ValueError
            return ret
        except (TypeError, ValueError):
            log.exception(
                "Error parsing discussion_blackouts %s for course %s",
                self.discussion_blackouts,
                self.id
            )
            return []

    @property
    def forum_posts_allowed(self):
        """
        Return whether forum posts are allowed by the discussion_blackouts
        setting
        """
        blackouts = self.get_discussion_blackout_datetimes()
        now = datetime.now(UTC())
        for blackout in blackouts:
            if blackout["start"] <= now <= blackout["end"]:
                return False
        return True

    @property
    def number(self):
        """
        Returns this course's number.

        This is a "number" in the sense of the "course numbers" that you see at
        lots of universities. For example, given a course
        "Intro to Computer Science" with the course key "edX/CS-101/2014", the
        course number would be "CS-101"
        """
        return course_metadata_utils.number_for_course_location(self.location)

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

    @property
    def video_pipeline_configured(self):
        """
        Returns whether the video pipeline advanced setting is configured for this course.
        """
        return (
            self.video_upload_pipeline is not None and
            'course_video_upload_token' in self.video_upload_pipeline
        )

    def clean_id(self, padding_char='='):
        """
        Returns a unique deterministic base32-encoded ID for the course.
        The optional padding_char parameter allows you to override the "=" character used for padding.
        """
        return course_metadata_utils.clean_course_key(self.location.course_key, padding_char)

    @property
    def teams_enabled(self):
        """
        Returns whether or not teams has been enabled for this course.

        Currently, teams are considered enabled when at least one topic has been configured for the course.
        """
        if self.teams_configuration:
            return len(self.teams_configuration.get('topics', [])) > 0
        return False

    @property
    def teams_max_size(self):
        """
        Returns the max size for teams if teams has been configured, else None.
        """
        return self.teams_configuration.get('max_team_size', None)

    @property
    def teams_topics(self):
        """
        Returns the topics that have been configured for teams for this course, else None.
        """
        return self.teams_configuration.get('topics', None)

    def get_user_partitions_for_scheme(self, scheme):
        """
        Retrieve all user partitions defined in the course for a particular
        partition scheme.

        Arguments:
            scheme (object): The user partition scheme.

        Returns:
            list of `UserPartition`

        """
        return [
            p for p in self.user_partitions
            if p.scheme == scheme
        ]

    def set_user_partitions_for_scheme(self, partitions, scheme):
        """
        Set the user partitions for a particular scheme.

        Preserves partitions associated with other schemes.

        Arguments:
            scheme (object): The user partition scheme.

        Returns:
            list of `UserPartition`

        """
        other_partitions = [
            p for p in self.user_partitions  # pylint: disable=access-member-before-definition
            if p.scheme != scheme
        ]
        self.user_partitions = other_partitions + partitions  # pylint: disable=attribute-defined-outside-init

    @property
    def can_toggle_course_pacing(self):
        """
        Whether or not the course can be set to self-paced at this time.

        Returns:
          bool: False if the course has already started, True otherwise.
        """
        return datetime.now(UTC()) <= self.start


class CourseSummary(object):
    """
    A lightweight course summary class, which constructs split/mongo course summary without loading
    the course. It is used at cms for listing courses to global staff user.
    """
    course_info_fields = ['display_name', 'display_coursenumber', 'display_organization']

    def __init__(self, course_locator, display_name=u"Empty", display_coursenumber=None, display_organization=None):
        """
        Initialize and construct course summary

        Arguments:
        course_locator (CourseLocator):  CourseLocator object of the course.

        display_name (unicode): display name of the course. When you create a course from console, display_name
        isn't set (course block has no key `display_name`). "Empty" name is returned when we load the course.
        If `display_name` isn't present in the course block, use the `Empty` as default display name.
        We can set None as a display_name in Course Advance Settings; Do not use "Empty" when display_name is
        set to None.

        display_coursenumber (unicode|None): Course number that is specified & appears in the courseware

        display_organization (unicode|None): Course organization that is specified & appears in the courseware

        """
        self.display_coursenumber = display_coursenumber
        self.display_organization = display_organization
        self.display_name = display_name

        self.id = course_locator  # pylint: disable=invalid-name
        self.location = course_locator.make_usage_key('course', 'course')

    @property
    def display_org_with_default(self):
        """
        Return a display organization if it has been specified, otherwise return the 'org' that
        is in the location
        """
        if self.display_organization:
            return self.display_organization
        return self.location.org

    @property
    def display_number_with_default(self):
        """
        Return a display course number if it has been specified, otherwise return the 'course' that
        is in the location
        """
        if self.display_coursenumber:
            return self.display_coursenumber
        return self.location.course
