"""
Declaration of CourseOverview model
"""

import json

import django.db.models
from django.db.models.fields import BooleanField, DateTimeField, DecimalField, TextField
from django.utils.translation import ugettext

from lms.djangoapps.certificates.api import get_active_web_certificate
from lms.djangoapps.courseware.courses import course_image_url
from util.date_utils import strftime_localized
from xmodule import course_metadata_utils
from xmodule.modulestore.django import modulestore
from xmodule_django.models import CourseKeyField, UsageKeyField


class CourseOverview(django.db.models.Model):
    """
    Model for storing and caching basic information about a course.

    This model contains basic course metadata such as an ID, display name,
    image URL, and any other information that would be necessary to display
    a course as part of a user dashboard or enrollment API.
    """

    # Course identification
    id = CourseKeyField(db_index=True, primary_key=True, max_length=255)  # pylint: disable=invalid-name
    _location = UsageKeyField(max_length=255)
    display_name = TextField(null=True)
    display_number_with_default = TextField()
    display_org_with_default = TextField()

    # Start/end dates
    start = DateTimeField(null=True)
    end = DateTimeField(null=True)
    advertised_start = TextField(null=True)

    # URLs
    course_image_url = TextField()
    facebook_url = TextField(null=True)
    social_sharing_url = TextField(null=True)
    end_of_course_survey_url = TextField(null=True)

    # Certification data
    certificates_display_behavior = TextField(null=True)
    certificates_show_before_end = BooleanField()
    has_any_active_web_certificate = BooleanField()
    cert_name_short = TextField()
    cert_name_long = TextField()

    # Grading
    lowest_passing_grade = DecimalField(max_digits=5, decimal_places=2)

    # Access parameters
    mobile_available = BooleanField()
    visible_to_staff_only = BooleanField()
    _pre_requisite_courses_json = TextField()  # JSON representation of list of CourseKey strings

    @staticmethod
    def _create_from_course(course):
        """
        Creates a CourseOverview object from a CourseDescriptor.

        Does not touch the database, simply constructs and returns an overview
        from the given course.

        Arguments:
            course (CourseDescriptor): any course descriptor object

        Returns:
            CourseOverview: overview extracted from the given course
        """
        return CourseOverview(
            id=course.id,
            _location=course.location,
            display_name=course.display_name,
            display_number_with_default=course.display_number_with_default,
            display_org_with_default=course.display_org_with_default,

            start=course.start,
            end=course.end,
            advertised_start=course.advertised_start,

            course_image_url=course_image_url(course),
            facebook_url=course.facebook_url,
            social_sharing_url=course.social_sharing_url,

            certificates_display_behavior=course.certificates_display_behavior,
            certificates_show_before_end=course.certificates_show_before_end,
            has_any_active_web_certificate=(get_active_web_certificate(course) is not None),
            cert_name_short=course.cert_name_short,
            cert_name_long=course.cert_name_long,
            lowest_passing_grade=course.lowest_passing_grade,
            end_of_course_survey_url=course.end_of_course_survey_url,

            mobile_available=course.mobile_available,
            visible_to_staff_only=course.visible_to_staff_only,
            _pre_requisite_courses_json=json.dumps(course.pre_requisite_courses)
        )

    @staticmethod
    def get_from_id(course_id):
        """
        Load a CourseOverview object for a given course ID.

        First, we try to load the CourseOverview from the database. If it
        doesn't exist, we load the entire course from the modulestore, create a
        CourseOverview object from it, and then cache it in the database for
        future use.

        Arguments:
            course_id (CourseKey): the ID of the course overview to be loaded

        Returns:
            CourseOverview: overview of the requested course
        """
        course_overview = None
        try:
            course_overview = CourseOverview.objects.get(id=course_id)
        except CourseOverview.DoesNotExist:
            store = modulestore()
            with store.bulk_operations(course_id):
                course = store.get_course(course_id)
                if course:
                    course_overview = CourseOverview._create_from_course(course)
                    course_overview.save()  # Save new overview to the cache
        return course_overview

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
