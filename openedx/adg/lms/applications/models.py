"""
All models for applications app
"""
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

from openedx.adg.common.util.date_utils import month_choices, year_choices


class ApplicationHub(TimeStampedModel):
    """
    Model for status of all required parts of user application submission.
    """
    user = models.OneToOneField(User, related_name='application_hub', on_delete=models.CASCADE, )
    is_prerequisite_courses_passed = models.BooleanField(default=False, )
    is_application_submitted = models.BooleanField(default=False, )
    is_assessment_completed = models.BooleanField(default=False, )

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return 'User {user_id}, application status id={id}'.format(user_id=self.user.id, id=self.id)


class UserApplication(TimeStampedModel):
    """
    Model for status of all required parts of user application submission.
    """
    user = models.OneToOneField(User, related_name='application', on_delete=models.CASCADE, )
    city = models.CharField(verbose_name=_('City'), max_length=255, )
    organization = models.CharField(verbose_name=_('Organization'), max_length=255, blank=True, )
    linkedin_url = models.URLField(max_length=255, blank=True, )
    resume = models.FileField(
        max_length=500, blank=True, null=True, upload_to='files/resume/',
        validators=[FileExtensionValidator(['pdf', 'doc', 'jpg', 'png'])],
        help_text=_('Accepted extensions: .pdf, .doc, .jpg, .png'),
    )
    cover_letter_file = models.FileField(
        max_length=500, blank=True, null=True, upload_to='files/cover_letter/',
        validators=[FileExtensionValidator(['pdf', 'doc', 'jpg', 'png'])],
        help_text=_('Accepted extensions: .pdf, .doc, .jpg, .png'),
    )
    cover_letter = models.TextField(blank=True, )

    class Meta:
        app_label = 'applications'
        verbose_name = _('User Application')
        verbose_name_plural = _('User Applications')

    def __str__(self):
        return 'UserApplication {id}, for user {email}'.format(id=self.id, email=self.user.email)


class Education(TimeStampedModel):
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

    month_choices = month_choices()
    year_choices = year_choices()

    user_application = models.ForeignKey(
        'UserApplication', related_name='education_set', related_query_name="education", on_delete=models.CASCADE,
    )
    name_of_school = models.CharField(verbose_name=_('Name of School / University'), max_length=255, )
    degree = models.CharField(verbose_name=_('Degree Received'), choices=DEGREE_TYPES, max_length=2, )
    ares_of_study = models.CharField(verbose_name=_('Area of Study'), max_length=255, blank=True)
    date_started_month = models.CharField(choices=month_choices, max_length=2, )
    date_started_year = models.IntegerField(choices=year_choices, )
    date_completed_month = models.CharField(choices=month_choices, blank=True, max_length=2, )
    date_completed_year = models.IntegerField(choices=year_choices, blank=True, null=True, )
    is_in_progress = models.BooleanField(verbose_name=_('In Progress'), default=False, )

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return 'Education {id}, for {degree}'.format(id=self.id, degree=self.degree)


class WorkExperience(TimeStampedModel):
    """
    Model for user work experience for application submission.
    """
    month_choices = month_choices()
    year_choices = year_choices()

    user_application = models.ForeignKey(
        'UserApplication', related_name='work_experiences', related_query_name="work_experience",
        on_delete=models.CASCADE,
    )
    name_of_organization = models.CharField(verbose_name=_('Name of Organization'), max_length=255, )
    job_position_title = models.CharField(verbose_name=_('Job Position / Title'), max_length=255, )
    date_started_month = models.CharField(choices=month_choices, max_length=2, )
    date_started_year = models.IntegerField(choices=year_choices, )
    date_completed_month = models.CharField(choices=month_choices, blank=True, max_length=2, )
    date_completed_year = models.IntegerField(choices=year_choices, blank=True, null=True, )
    is_current_position = models.BooleanField(verbose_name=_('Current Position'), default=False, )
    job_responsibilities = models.TextField(verbose_name=_('Job Responsibilities'), blank=True, )

    class Meta:
        app_label = 'applications'

    def __str__(self):
        return 'WorkExperience {id}, for {organization}'.format(id=self.id, organization=self.name_of_organization)
