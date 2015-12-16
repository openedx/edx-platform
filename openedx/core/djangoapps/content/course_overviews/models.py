"""
Declaration of CourseOverview model
"""
import json
import logging

from django.db import models, transaction
from django.db.models.fields import BooleanField, DateTimeField, DecimalField, TextField, FloatField, IntegerField
from django.db.utils import IntegrityError
from django.template import defaultfilters
from django.utils.translation import ugettext
from lms.djangoapps import django_comment_client
from model_utils.models import TimeStampedModel
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.models.course_details import CourseDetails

from util.date_utils import strftime_localized
from xmodule import course_metadata_utils
from xmodule.course_module import CourseDescriptor, DEFAULT_START_DATE
from xmodule.error_module import ErrorDescriptor
from xmodule.modulestore.django import modulestore
from xmodule_django.models import CourseKeyField, UsageKeyField

from ccx_keys.locator import CCXLocator


log = logging.getLogger(__name__)


class CourseOverview(TimeStampedModel):
    """
    Model for storing and caching basic information about a course.

    This model contains basic course metadata such as an ID, display name,
    image URL, and any other information that would be necessary to display
    a course as part of:
        user dashboard (enrolled courses)
        course catalog (courses to enroll in)
        course about (meta data about the course)
    """

    class Meta(object):
        app_label = 'course_overviews'

    # IMPORTANT: Bump this whenever you modify this model and/or add a migration.
    VERSION = 3

    # Cache entry versioning.
    version = IntegerField()

    # Course identification
    id = CourseKeyField(db_index=True, primary_key=True, max_length=255)
    _location = UsageKeyField(max_length=255)
    org = TextField(max_length=255, default='outdated_entry')
    display_name = TextField(null=True)
    display_number_with_default = TextField()
    display_org_with_default = TextField()

    # Start/end dates
    start = DateTimeField(null=True)
    end = DateTimeField(null=True)
    advertised_start = TextField(null=True)
    announcement = DateTimeField(null=True)

    # URLs
    course_image_url = TextField()
    facebook_url = TextField(null=True)
    social_sharing_url = TextField(null=True)
    end_of_course_survey_url = TextField(null=True)

    # Certification data
    certificates_display_behavior = TextField(null=True)
    certificates_show_before_end = BooleanField(default=False)
    cert_html_view_enabled = BooleanField(default=False)
    has_any_active_web_certificate = BooleanField(default=False)
    cert_name_short = TextField()
    cert_name_long = TextField()

    # Grading
    lowest_passing_grade = DecimalField(max_digits=5, decimal_places=2, null=True)

    # Access parameters
    days_early_for_beta = FloatField(null=True)
    mobile_available = BooleanField(default=False)
    visible_to_staff_only = BooleanField(default=False)
    _pre_requisite_courses_json = TextField()  # JSON representation of list of CourseKey strings

    # Enrollment details
    enrollment_start = DateTimeField(null=True)
    enrollment_end = DateTimeField(null=True)
    enrollment_domain = TextField(null=True)
    invitation_only = BooleanField(default=False)
    max_student_enrollments_allowed = IntegerField(null=True)

    # Catalog information
    catalog_visibility = TextField(null=True)
    short_description = TextField(null=True)
    course_video_url = TextField(null=True)
    effort = TextField(null=True)

    @classmethod
    def _create_from_course(cls, course):
        """
        Creates a CourseOverview object from a CourseDescriptor.

        Does not touch the database, simply constructs and returns an overview
        from the given course.

        Arguments:
            course (CourseDescriptor): any course descriptor object

        Returns:
            CourseOverview: overview extracted from the given course
        """
        from lms.djangoapps.certificates.api import get_active_web_certificate
        from openedx.core.lib.courses import course_image_url

        log.info('Creating course overview for %s.', unicode(course.id))

        # Workaround for a problem discovered in https://openedx.atlassian.net/browse/TNL-2806.
        # If the course has a malformed grading policy such that
        # course._grading_policy['GRADE_CUTOFFS'] = {}, then
        # course.lowest_passing_grade will raise a ValueError.
        # Work around this for now by defaulting to None.
        try:
            lowest_passing_grade = course.lowest_passing_grade
        except ValueError:
            lowest_passing_grade = None

        display_name = course.display_name
        start = course.start
        end = course.end
        max_student_enrollments_allowed = course.max_student_enrollments_allowed
        if isinstance(course.id, CCXLocator):
            from lms.djangoapps.ccx.utils import get_ccx_from_ccx_locator
            ccx = get_ccx_from_ccx_locator(course.id)
            display_name = ccx.display_name
            start = ccx.start
            end = ccx.due
            max_student_enrollments_allowed = ccx.max_student_enrollments_allowed

        return cls(
            version=cls.VERSION,
            id=course.id,
            _location=course.location,
            org=course.location.org,
            display_name=display_name,
            display_number_with_default=course.display_number_with_default,
            display_org_with_default=course.display_org_with_default,

            start=start,
            end=end,
            advertised_start=course.advertised_start,
            announcement=course.announcement,

            course_image_url=course_image_url(course),
            facebook_url=course.facebook_url,
            social_sharing_url=course.social_sharing_url,

            certificates_display_behavior=course.certificates_display_behavior,
            certificates_show_before_end=course.certificates_show_before_end,
            cert_html_view_enabled=course.cert_html_view_enabled,
            has_any_active_web_certificate=(get_active_web_certificate(course) is not None),
            cert_name_short=course.cert_name_short,
            cert_name_long=course.cert_name_long,
            lowest_passing_grade=lowest_passing_grade,
            end_of_course_survey_url=course.end_of_course_survey_url,

            days_early_for_beta=course.days_early_for_beta,
            mobile_available=course.mobile_available,
            visible_to_staff_only=course.visible_to_staff_only,
            _pre_requisite_courses_json=json.dumps(course.pre_requisite_courses),

            enrollment_start=course.enrollment_start,
            enrollment_end=course.enrollment_end,
            enrollment_domain=course.enrollment_domain,
            invitation_only=course.invitation_only,
            max_student_enrollments_allowed=max_student_enrollments_allowed,

            catalog_visibility=course.catalog_visibility,
            short_description=CourseDetails.fetch_about_attribute(course.id, 'short_description'),
            effort=CourseDetails.fetch_about_attribute(course.id, 'effort'),
            course_video_url=CourseDetails.fetch_video_url(course.id),
        )

    @classmethod
    def load_from_module_store(cls, course_id):
        """
        Load a CourseDescriptor, create a new CourseOverview from it, cache the
        overview, and return it.

        Arguments:
            course_id (CourseKey): the ID of the course overview to be loaded.

        Returns:
            CourseOverview: overview of the requested course.

        Raises:
            - CourseOverview.DoesNotExist if the course specified by course_id
                was not found.
            - IOError if some other error occurs while trying to load the
                course from the module store.
        """
        store = modulestore()
        with store.bulk_operations(course_id):
            course = store.get_course(course_id)
            if isinstance(course, CourseDescriptor):
                course_overview = cls._create_from_course(course)
                try:
                    with transaction.atomic():
                        course_overview.save()
                        CourseOverviewTab.objects.bulk_create([
                            CourseOverviewTab(tab_id=tab.tab_id, course_overview=course_overview)
                            for tab in course.tabs
                        ])
                except IntegrityError:
                    # There is a rare race condition that will occur if
                    # CourseOverview.get_from_id is called while a
                    # another identical overview is already in the process
                    # of being created.
                    # One of the overviews will be saved normally, while the
                    # other one will cause an IntegrityError because it tries
                    # to save a duplicate.
                    # (see: https://openedx.atlassian.net/browse/TNL-2854).
                    pass
                return course_overview
            elif course is not None:
                raise IOError(
                    "Error while loading course {} from the module store: {}",
                    unicode(course_id),
                    course.error_msg if isinstance(course, ErrorDescriptor) else unicode(course)
                )
            else:
                raise cls.DoesNotExist()

    @classmethod
    def get_from_id(cls, course_id):
        """
        Load a CourseOverview object for a given course ID.

        First, we try to load the CourseOverview from the database. If it
        doesn't exist, we load the entire course from the modulestore, create a
        CourseOverview object from it, and then cache it in the database for
        future use.

        Arguments:
            course_id (CourseKey): the ID of the course overview to be loaded.

        Returns:
            CourseOverview: overview of the requested course.

        Raises:
            - CourseOverview.DoesNotExist if the course specified by course_id
                was not found.
            - IOError if some other error occurs while trying to load the
                course from the module store.
        """
        try:
            course_overview = cls.objects.get(id=course_id)
            if course_overview.version < cls.VERSION:
                # Throw away old versions of CourseOverview, as they might contain stale data.
                course_overview.delete()
                course_overview = None
        except cls.DoesNotExist:
            course_overview = None
        return course_overview or cls.load_from_module_store(course_id)

    def clean_id(self, padding_char='='):
        """
        Returns a unique deterministic base32-encoded ID for the course.

        Arguments:
            padding_char (str): Character used for padding at end of base-32
                                -encoded string, defaulting to '='
        """
        return course_metadata_utils.clean_course_key(self.location.course_key, padding_char)

    @property
    def location(self):
        """
        Returns the UsageKey of this course.

        UsageKeyField has a strange behavior where it fails to parse the "run"
        of a course out of the serialized form of a Mongo Draft UsageKey. This
        method is a wrapper around _location attribute that fixes the problem
        by calling map_into_course, which restores the run attribute.
        """
        if self._location.run is None:
            self._location = self._location.map_into_course(self.id)
        return self._location

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
    def url_name(self):
        """
        Returns this course's URL name.
        """
        return course_metadata_utils.url_name_for_course_location(self.location)

    @property
    def display_name_with_default(self):
        """
        Return reasonable display name for the course.
        """
        return course_metadata_utils.display_name_with_default(self)

    def has_started(self):
        """
        Returns whether the the course has started.
        """
        return course_metadata_utils.has_course_started(self.start)

    def has_ended(self):
        """
        Returns whether the course has ended.
        """
        return course_metadata_utils.has_course_ended(self.end)

    def starts_within(self, days):
        """
        Returns True if the course starts with-in given number of days otherwise returns False.
        """

        return course_metadata_utils.course_starts_within(self.start, days)

    def start_datetime_text(self, format_string="SHORT_DATE"):
        """
        Returns the desired text corresponding the course's start date and
        time in UTC.  Prefers .advertised_start, then falls back to .start.
        """
        return course_metadata_utils.course_start_datetime_text(
            self.start,
            self.advertised_start,
            format_string,
            ugettext,
            strftime_localized
        )

    @property
    def start_date_is_still_default(self):
        """
        Checks if the start date set for the course is still default, i.e.
        .start has not been modified, and .advertised_start has not been set.
        """
        return course_metadata_utils.course_start_date_is_default(
            self.start,
            self.advertised_start,
        )

    def end_datetime_text(self, format_string="SHORT_DATE"):
        """
        Returns the end date or datetime for the course formatted as a string.
        """
        return course_metadata_utils.course_end_datetime_text(
            self.end,
            format_string,
            strftime_localized
        )

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

    @property
    def start_type(self):
        """
        Returns the type of the course's 'start' field.
        """
        if self.advertised_start:
            return u'string'
        elif self.start != DEFAULT_START_DATE:
            return u'timestamp'
        else:
            return u'empty'

    @property
    def start_display(self):
        """
        Returns the display value for the course's start date.
        """
        if self.advertised_start:
            return self.advertised_start
        elif self.start != DEFAULT_START_DATE:
            return defaultfilters.date(self.start, "DATE_FORMAT")
        else:
            return None

    def may_certify(self):
        """
        Returns whether it is acceptable to show the student a certificate
        download link.
        """
        return course_metadata_utils.may_certify_for_course(
            self.certificates_display_behavior,
            self.certificates_show_before_end,
            self.has_ended()
        )

    @property
    def pre_requisite_courses(self):
        """
        Returns a list of ID strings for this course's prerequisite courses.
        """
        return json.loads(self._pre_requisite_courses_json)

    @classmethod
    def get_select_courses(cls, course_keys):
        """
        Returns CourseOverview objects for the given course_keys.
        """
        course_overviews = []

        log.info('Generating course overview for %d courses.', len(course_keys))
        log.debug('Generating course overview(s) for the following courses: %s', course_keys)

        for course_key in course_keys:
            try:
                course_overviews.append(CourseOverview.get_from_id(course_key))
            except Exception as ex:  # pylint: disable=broad-except
                log.exception(
                    'An error occurred while generating course overview for %s: %s',
                    unicode(course_key),
                    ex.message,
                )

        log.info('Finished generating course overviews.')

        return course_overviews

    @classmethod
    def get_all_courses(cls, org=None):
        """
        Returns all CourseOverview objects in the database.

        Arguments:
            org (string): Optional parameter that allows filtering
                by organization.
        """
        # Note: If a newly created course is not returned in this QueryList,
        # make sure the "publish" signal was emitted when the course was
        # created.  For tests using CourseFactory, use emit_signals=True.
        course_overviews = CourseOverview.objects.all()
        if org:
            course_overviews = course_overviews.filter(org=org)
        return course_overviews

    @classmethod
    def get_all_course_keys(cls):
        """
        Returns all course keys from course overviews.
        """
        return [
            CourseKey.from_string(course_overview['id'])
            for course_overview in CourseOverview.objects.values('id')
        ]

    def is_discussion_tab_enabled(self):
        """
        Returns True if course has discussion tab and is enabled
        """
        tabs = self.tabs.all()
        # creates circular import; hence explicitly referenced is_discussion_enabled
        for tab in tabs:
            if tab.tab_id == "discussion" and django_comment_client.utils.is_discussion_enabled(self.id):
                return True
        return False


class CourseOverviewTab(models.Model):
    """
    Model for storing and caching tabs information of a course.
    """
    tab_id = models.CharField(max_length=50)
    course_overview = models.ForeignKey(CourseOverview, db_index=True, related_name="tabs")
