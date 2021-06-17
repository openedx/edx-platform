"""
All models for applications app
"""
from datetime import date

from django.contrib.auth.models import Group, User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from common.djangoapps.student.models import UserProfile
from openedx.adg.lms.utils.date_utils import month_choices
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from .constants import ALLOWED_LOGO_EXTENSIONS
from .helpers import get_user_scores_for_courses, max_year_value_validator, min_year_value_validator, validate_logo_size
from .managers import MultilingualCourseGroupManager, MultilingualCourseManager, SubmittedApplicationsManager


class ApplicationHub(TimeStampedModel):
    """
    Model for status of all required parts of user application submission.
    """

    TOTAL_APPLICATION_OBJECTIVES = 2

    user = models.OneToOneField(
        User, related_name='application_hub', on_delete=models.CASCADE, verbose_name=_('User'),
    )
    is_prerequisite_courses_passed = models.BooleanField(default=False, verbose_name=_('Prerequisite Courses Passed'), )
    is_bu_prerequisite_courses_passed = models.BooleanField(
        default=False, verbose_name=_('Business Unit Prerequisite Courses Passed'),
    )
    is_written_application_completed = models.BooleanField(
        default=False, verbose_name=_('Written Application Submitted'),
    )
    submission_date = models.DateField(null=True, blank=True, verbose_name=_('Submission Date'), )

    class Meta:
        app_label = 'applications'

    def set_is_prerequisite_courses_passed(self):
        """
        Mark pre_req_course objective as complete i.e set is_prerequisite_courses_passed to True.
        """
        self.is_prerequisite_courses_passed = True
        self.save()

    def set_is_bu_prerequisite_courses_passed(self):
        """
        Mark business line courses objective as complete i.e set is_bu_prerequisite_courses_passed to True.
        """
        self.is_bu_prerequisite_courses_passed = True
        self.save()

    def submit_written_application_for_current_date(self):
        """
        Mark written_application objective as complete i.e set is_written_application_completed to True and add current
        date as submission_date.
        """
        self.is_written_application_completed = True
        self.submission_date = date.today()
        self.save()

    def are_application_pre_reqs_completed(self):
        """
        Check if all the application objectives are completed or not.

        Returns:
            bool: True if all objectives are done, otherwise False.
        """
        return (self.is_prerequisite_courses_passed and self.is_written_application_completed and
                self.is_bu_prerequisite_courses_passed)

    @property
    def progress_of_objectives_completed_in_float(self):
        """
        Property to return percentage of the total objectives completed.

        Returns:
            str: percentage in string
        """
        number_of_objectives_completed = sum([self.is_written_application_completed,
                                              self.is_prerequisite_courses_passed])
        return number_of_objectives_completed / self.TOTAL_APPLICATION_OBJECTIVES

    @property
    def is_written_application_started(self):
        """
        Check if user has started the application or not

        Returns:
            True or False.
        """
        return hasattr(self.user, 'application')

    @property
    def are_program_and_bu_prereq_courses_completed(self):
        """
        Checks if both the program and the business unit prerequisite courses have been completed

        Returns:
             Boolean: True if prereq courses are passed and False otherwise
        """
        return self.is_prerequisite_courses_passed and self.is_bu_prerequisite_courses_passed

    def __str__(self):
        return 'User {user_id}, application status id={id}'.format(user_id=self.user_id, id=self.id)


class BusinessLine(TimeStampedModel):
    """
    Model to save the business lines
    """

    title = models.CharField(verbose_name=_('Title'), max_length=150, unique=True, )
    logo = models.ImageField(
        upload_to='business-lines/logos/', verbose_name=_('Logo'),
        validators=[FileExtensionValidator(ALLOWED_LOGO_EXTENSIONS), validate_logo_size],
        help_text=_('Accepted extensions: .png, .jpg, .svg'),
    )
    description = models.TextField(verbose_name=_('Description'), )
    group = models.OneToOneField(
        Group, related_name='business_line', on_delete=models.CASCADE, null=True
    )
    site_url = models.URLField(default='', verbose_name=_('Site URL'))

    class Meta:
        app_label = 'applications'

    @classmethod
    def is_user_business_line_admin(cls, user):
        """
        Checks if the user is a business line admin i.e Belongs to at least one business line group

        Arguments:
             user (User): User object to check permissions for

        Returns:
            boolean: Returns True if the user is an admin and False if not
        """
        return cls.objects.filter(group__user=user).exists()

    def __str__(self):
        return '{}'.format(self.title)


class UserApplication(TimeStampedModel):
    """
    Model for status of all required parts of user application submission.
    """

    user = models.OneToOneField(User, related_name='application', on_delete=models.CASCADE, verbose_name=_('User'), )
    business_line = models.ForeignKey(BusinessLine, verbose_name=_('Business Line'),
                                      on_delete=models.CASCADE, null=True, blank=True, )

    organization = models.CharField(verbose_name=_('Organization'), max_length=255, blank=True, )
    linkedin_url = models.URLField(verbose_name=_('LinkedIn URL'), max_length=255, blank=True, )
    interest_in_business = models.TextField(
        blank=True, verbose_name=_('Why are you interested in this business line?'),
    )
    is_work_experience_not_applicable = models.BooleanField(
        verbose_name=_('Work Experience Not Applicable'),
        default=False
    )
    background_question = models.TextField(blank=True, verbose_name=_('Background Question'))

    OPEN = 'open'
    WAITLIST = 'waitlist'
    ACCEPTED = 'accepted'

    STATUS_CHOICES = (
        (OPEN, _('Open')),
        (WAITLIST, _('Waitlist')),
        (ACCEPTED, _('Accepted'))
    )
    status = models.CharField(
        verbose_name=_('Application Status'), choices=STATUS_CHOICES, max_length=8, default=OPEN,
    )
    reviewed_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.CASCADE, verbose_name=_('Reviewed By')
    )
    internal_admin_note = models.TextField(blank=True, verbose_name=_('Admin Note'))

    objects = models.Manager()
    submitted_applications = SubmittedApplicationsManager()

    class Meta:
        app_label = 'applications'
        verbose_name = _('Application')
        ordering = ['created']

    def __str__(self):
        return '{}'.format(self.user.profile.name)  # pylint: disable=E1101

    @property
    def program_prereq_course_scores(self):
        """
        Fetch and return applicant scores in the pre-requisite courses of the franchise program.

        Returns:
            list: Prereq course name and score pairs
        """
        program_prereq_course_overviews = MultilingualCourseGroup.objects.get_user_program_prereq_courses(self.user)
        scores_in_program_prereq_courses = get_user_scores_for_courses(self.user, program_prereq_course_overviews)
        return scores_in_program_prereq_courses

    @property
    def bu_prereq_course_scores(self):
        """
        Fetch and return applicant scores in the business unit pre-requisite courses. This
        includes both common and business line specific prereq courses

        Returns:
            list: Prereq course name and score pairs
        """
        bu_prereq_course_overviews = MultilingualCourseGroup.objects. \
            get_user_business_line_and_common_business_line_prereq_courses(self.user)

        scores_in_bu_prereq_courses = get_user_scores_for_courses(self.user, bu_prereq_course_overviews)
        return scores_in_bu_prereq_courses

    @property
    def has_work_experience(self):
        """
        Check if any work experience is associated with the user application
        """
        return self.applications_workexperiences.exists()

    @property
    def has_no_work_experience(self):
        """
        Check if no work experience is associated with the user application.

        Returns:
            bool: True if no work experience is associated with the application, False otherwise
        """
        return not self.has_work_experience

    @property
    def is_education_completed(self):
        """
        Check if any education is associated with the user application.
        """
        return self.applications_educations.exists()

    @property
    def is_work_experience_completed(self):
        """
        Check if user added any work experience or marked user application as work experience not applicable
        """
        return self.is_work_experience_not_applicable or self.has_work_experience

    @property
    def is_reference_added(self):
        """
        Check if user has added any reference against their application
        """
        return self.references.exists()

    @property
    def is_education_experience_completed(self):
        """
        Check user completed the education and experience step in user application
        """
        return self.is_education_completed and self.is_work_experience_completed \
            and bool(self.background_question) and self.is_reference_added


class UserStartAndEndDates(TimeStampedModel):
    """
    An abstract model for start and end dates.
    """

    month_choices = month_choices(default_title='Month')

    user_application = models.ForeignKey(
        'UserApplication', related_name='%(app_label)s_%(class)ss', related_query_name='%(app_label)s_%(class)s',
        on_delete=models.CASCADE,
    )
    date_started_month = models.IntegerField(verbose_name=_('Start Month'), choices=month_choices, )
    date_completed_month = models.IntegerField(
        verbose_name=_('Completed Month'), choices=month_choices, blank=True, null=True,
    )
    date_started_year = models.IntegerField(
        verbose_name=_('Start Year'),
        validators=(min_year_value_validator, max_year_value_validator)
    )
    date_completed_year = models.IntegerField(
        verbose_name=_('Completed Year'), blank=True, null=True,
        validators=(min_year_value_validator, max_year_value_validator)
    )

    class Meta(object):
        abstract = True


class Education(UserStartAndEndDates):
    """
    Model for user education qualification for application submission.
    """

    HIGH_SCHOOL_DIPLOMA = 'HD'
    ASSOCIATE_DEGREE = 'AD'
    BACHELOR_DEGREE = 'BD'
    MASTERS_DEGREE = 'MD'
    DOCTORAL_DEGREE = 'DD'

    DEGREE_TYPES = [
        (HIGH_SCHOOL_DIPLOMA, _('High School Diploma or GED')),
        (ASSOCIATE_DEGREE, _('Associate Degree')),
        (BACHELOR_DEGREE, _('Bachelor’s Degree')),
        (MASTERS_DEGREE, _('Master’s Degree')),
        (DOCTORAL_DEGREE, _('Doctoral Degree')),
    ]

    name_of_school = models.CharField(verbose_name=_('School / University'), max_length=255, )
    degree = models.CharField(verbose_name=_('Degree Received'), choices=DEGREE_TYPES, max_length=2, )
    area_of_study = models.CharField(verbose_name=_('Area of Study'), max_length=255, blank=True, )
    is_in_progress = models.BooleanField(verbose_name=_('In Progress'), default=False, )

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return ''


class WorkExperience(UserStartAndEndDates):
    """
    Model for user work experience for application submission.
    """

    name_of_organization = models.CharField(verbose_name=_('Organization'), max_length=255, )
    job_position_title = models.CharField(verbose_name=_('Job Position / Title'), max_length=255, )
    is_current_position = models.BooleanField(verbose_name=_('Current Position'), default=False, )
    job_responsibilities = models.TextField(verbose_name=_('Job Responsibilities'), )

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return ''


class MultilingualCourseGroup(models.Model):
    """
    Model for multilingual course groups
    """

    name = models.CharField(verbose_name=_('Course group name'), max_length=255, )

    is_program_prerequisite = models.BooleanField(
        default=False,
        verbose_name=_('Is Prerequisite for the Program'),
    )
    is_common_business_line_prerequisite = models.BooleanField(
        default=False,
        verbose_name=_('Is Common Prerequisite for all Business Lines')
    )
    business_line_prerequisite = models.ForeignKey(
        BusinessLine,
        default=None,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='prerequisite_courses',
        related_query_name="prerequisite_course",
        verbose_name=_('Is Prerequisite for Business Line'),
        help_text=_('Select the Business Line that this Course Group is a prerequisite for')
    )

    objects = MultilingualCourseGroupManager()

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return self.name

    @property
    def is_business_line_prerequisite(self):
        return bool(self.business_line_prerequisite)

    def multilingual_course_count(self):
        return self.multilingual_courses.count()

    # pylint: disable=no-member
    def open_multilingual_courses_count(self):
        return self.multilingual_courses.open_multilingual_courses().count()

    def open_multilingual_course_keys(self):
        return self.multilingual_courses.open_multilingual_courses().values_list('course', flat=True)
    # pylint: enable=no-member


class MultilingualCourse(models.Model):
    """
    Model for multilingual courses
    """

    course = models.OneToOneField(
        CourseOverview,
        on_delete=models.CASCADE,
        related_name='multilingual_course',
        unique=True,
        verbose_name=_('Multilingual version of a course'),
    )
    multilingual_course_group = models.ForeignKey(
        MultilingualCourseGroup,
        on_delete=models.CASCADE,
        related_name='multilingual_courses',
    )

    objects = MultilingualCourseManager()

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return 'id={id} name={name}'.format(id=self.course.id, name=self.course.display_name)


class Reference(models.Model):
    """
    Model for references provided by applicants
    """

    name = models.CharField(verbose_name=_('Name'), max_length=255)
    position = models.CharField(verbose_name=_('Job Position / Title'), max_length=255)
    relationship = models.CharField(verbose_name=_('Relationship to you'), max_length=255)
    phone_number = models.CharField(validators=[UserProfile.phone_regex], max_length=50)
    email = models.EmailField(verbose_name=_('Email'), blank=True)

    user_application = models.ForeignKey(
        UserApplication, related_name='references', related_query_name='reference', on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return self.name
