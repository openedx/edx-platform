"""
Models for bulk email

WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms schemamigration bulk_email --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/bulk_email/migrations/

"""
import logging
import markupsafe

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from openedx.core.lib.html_to_text import html_to_text
from openedx.core.lib.mail_utils import wrap_message

from config_models.models import ConfigurationModel
from student.roles import CourseStaffRole, CourseInstructorRole

from xmodule_django.models import CourseKeyField

from util.keyword_substitution import substitute_keywords_with_data
from util.query import use_read_replica_if_available

log = logging.getLogger(__name__)

class Email(models.Model):
    """
    Abstract base class for common information for an email.
    """
    sender = models.ForeignKey(User, default=1, blank=True, null=True)
    slug = models.CharField(max_length=128, db_index=True)
    subject = models.CharField(max_length=128, blank=True)
    html_message = models.TextField(null=True, blank=True)
    text_message = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta(object):
        app_label = "bulk_email"
        abstract = True


# Bulk email targets - the send to options that users can select from when they send email.
SEND_TO_MYSELF = 'myself'
SEND_TO_STAFF = 'staff'
SEND_TO_LEARNERS = 'learners'
SEND_TO_COHORT = 'cohort'
SEND_TO_ALL = 'all'
EMAIL_TARGETS = [SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_LEARNERS, SEND_TO_COHORT, SEND_TO_ALL]
EMAIL_TARGET_DESCRIPTIONS = ['Myself', 'Staff and instructors', 'All students', 'Specific cohort', 'All']
EMAIL_TARGET_CHOICES = zip(EMAIL_TARGETS, EMAIL_TARGET_DESCRIPTIONS)


class Target(models.Model):
    """
    A way to refer to a particular group (within a course) as a "Send to:" target.
    """
    target_type = models.CharField(max_length=64, choices=EMAIL_TARGET_CHOICES)

    class Meta(object):
        app_label = "bulk_email"

    def __unicode__(self):
        return "CourseEmail Target for: {}".format(self.target_type)

    def get_users(self, course_id, user_id=None):
        staff_qset = CourseStaffRole(course_id).users_with_role()
        instructor_qset = CourseInstructorRole(course_id).users_with_role()
        staff_instructor_qset = (staff_qset | instructor_qset)
        enrollment_qset = User.objects.filter(
           is_active=True,
           courseenrollment__course_id=course_id,
           courseenrollment__is_active=True
        )
        if self.target_type == SEND_TO_MYSELF:
            if user_id is None:
                raise ValueError("Must define self user to send email to self.")
            user = User.objects.filter(id=user_id)
            return use_read_replica_if_available(user)
        elif self.target_type == SEND_TO_STAFF:
            return use_read_replica_if_available(staff_instructor_qset)
        elif self.target_type == SEND_TO_LEARNERS:
            if staff_instructor_qset.count() <= 0:
                return use_read_replica_if_available(enrollment_qset)
            return use_read_replica_if_available(enrollment_qset.exclude(staff_instructor_qset)),
        elif self.target_type == SEND_TO_COHORT:
            return self.cohort.users  # TODO: cohorts aren't hooked up, this may not work
        elif self.target_type == SEND_TO_ALL:
            # Return both learners and staff
            recipient_qsets = [
                use_read_replica_if_available(staff_instructor_qset),
                use_read_replica_if_available(enrollment_qset),
            ]
            return recipient_qsets
        else:
            raise ValueError("Unrecognized target type {}".format(self.target_type))


class CohortTarget(Target):
    """
    Subclass of Target, specifically referring to a cohort.
    """
    cohort = models.ForeignKey('course_groups.CourseUserGroup')

    class Meta:
        app_label = "bulk_email"

    def __init__(self, *args, **kwargs):
        kwargs['target_type'] = SEND_TO_COHORT
        super(CohortTarget, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return "CourseEmail CohortTarget: {}".format(self.cohort.id)

    @classmethod
    def ensure_valid_cohort(cls, cohort_name, course_id):
        """
        Ensures cohort_name is a valid cohort for course_id.

        Returns the cohort if valid, raises an error otherwise.
        """
        if cohort_name is None:
            raise ValueError("Cannot create a CohortTarget without specifying a cohort_name.")
        try:
            cohort = CourseUserGroup.get(name=cohort_name, course_id=course_id)
        except CourseUserGroup.DoesNotExist:
            raise ValueError(
                "Cohort {cohort} does not exist in course {course_id}".format(
                    cohort=cohort_name,
                    course_id=course_id
                )
            )
        return cohort


class CourseEmail(Email):
    """
    Stores information for an email to a course.
    """
    class Meta(object):
        app_label = "bulk_email"

    course_id = CourseKeyField(max_length=255, db_index=True)
    targets = models.ManyToManyField(Target)
    template_name = models.CharField(null=True, max_length=255)
    from_addr = models.CharField(null=True, max_length=255)

    def __unicode__(self):
        return self.subject

    @classmethod
    def create(
            cls, course_id, sender, targets, subject, html_message,
            text_message=None, template_name=None, from_addr=None, cohort_name=None):
        """
        Create an instance of CourseEmail.
        """
        # automatically generate the stripped version of the text from the HTML markup:
        if text_message is None:
            text_message = html_to_text(html_message)

        #from nose.tools import set_trace; set_trace()
        new_targets = []
        for target in targets:
            # Ensure our desired target exists
            if target not in EMAIL_TARGETS:
                fmt = 'Course email being sent to unrecognized target: "{target}" for "{course}", subject "{subject}"'
                msg = fmt.format(target=target, course=course_id, subject=subject)
                raise ValueError(msg)
            elif target == SEND_TO_COHORT:
                cohort = CohortTarget.ensure_valid_cohort(cohort_name, course_id)
                new_target, _ = CohortTarget.objects.get_or_create(target_type=target, cohort=cohort)
            else:
                new_target, _ = Target.objects.get_or_create(target_type=target)
            new_targets.append(new_target)

        # create the task, then save it immediately:
        course_email = cls(
            course_id=course_id,
            sender=sender,
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            template_name=template_name,
            from_addr=from_addr,
        )
        course_email.save()  # Must exist in db before setting M2M relationship values
        course_email.targets.add(*new_targets)
        course_email.save()

        return course_email

    def get_template(self):
        """
        Returns the corresponding CourseEmailTemplate for this CourseEmail.
        """
        return CourseEmailTemplate.get_template(name=self.template_name)


class Optout(models.Model):
    """
    Stores users that have opted out of receiving emails from a course.
    """
    # Allowing null=True to support data migration from email->user.
    # We need to first create the 'user' column with some sort of default in order to run the data migration,
    # and given the unique index, 'null' is the best default value.
    user = models.ForeignKey(User, db_index=True, null=True)
    course_id = CourseKeyField(max_length=255, db_index=True)

    class Meta(object):
        app_label = "bulk_email"
        unique_together = ('user', 'course_id')


# Defines the tag that must appear in a template, to indicate
# the location where the email message body is to be inserted.
COURSE_EMAIL_MESSAGE_BODY_TAG = '{{message_body}}'


class CourseEmailTemplate(models.Model):
    """
    Stores templates for all emails to a course to use.

    This is expected to be a singleton, to be shared across all courses.
    Initialization takes place in a migration that in turn loads a fixture.
    The admin console interface disables add and delete operations.
    Validation is handled in the CourseEmailTemplateForm class.
    """
    class Meta(object):
        app_label = "bulk_email"

    html_template = models.TextField(null=True, blank=True)
    plain_template = models.TextField(null=True, blank=True)
    name = models.CharField(null=True, max_length=255, unique=True, blank=True)

    @staticmethod
    def get_template(name=None):
        """
        Fetch the current template

        If one isn't stored, an exception is thrown.
        """
        try:
            return CourseEmailTemplate.objects.get(name=name)
        except CourseEmailTemplate.DoesNotExist:
            log.exception("Attempting to fetch a non-existent course email template")
            raise

    @staticmethod
    def _render(format_string, message_body, context):
        """
        Create a text message using a template, message body and context.

        Convert message body (`message_body`) into an email message
        using the provided template.  The template is a format string,
        which is rendered using format() with the provided `context` dict.

        Any keywords encoded in the form %%KEYWORD%% found in the message
        body are substituted with user data before the body is inserted into
        the template.

        Output is returned as a unicode string.  It is not encoded as utf-8.
        Such encoding is left to the email code, which will use the value
        of settings.DEFAULT_CHARSET to encode the message.
        """

        # Substitute all %%-encoded keywords in the message body
        if 'user_id' in context and 'course_id' in context:
            message_body = substitute_keywords_with_data(message_body, context)

        result = format_string.format(**context)

        # Note that the body tag in the template will now have been
        # "formatted", so we need to do the same to the tag being
        # searched for.
        message_body_tag = COURSE_EMAIL_MESSAGE_BODY_TAG.format()
        result = result.replace(message_body_tag, message_body, 1)

        # finally, return the result, after wrapping long lines and without converting to an encoded byte array.
        return wrap_message(result)

    def render_plaintext(self, plaintext, context):
        """
        Create plain text message.

        Convert plain text body (`plaintext`) into plaintext email message using the
        stored plain template and the provided `context` dict.
        """
        return CourseEmailTemplate._render(self.plain_template, plaintext, context)

    def render_htmltext(self, htmltext, context):
        """
        Create HTML text message.

        Convert HTML text body (`htmltext`) into HTML email message using the
        stored HTML template and the provided `context` dict.
        """
        # HTML-escape string values in the context (used for keyword substitution).
        for key, value in context.iteritems():
            if isinstance(value, basestring):
                context[key] = markupsafe.escape(value)
        return CourseEmailTemplate._render(self.html_template, htmltext, context)


class CourseAuthorization(models.Model):
    """
    Enable the course email feature on a course-by-course basis.
    """
    class Meta(object):
        app_label = "bulk_email"

    # The course that these features are attached to.
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True)

    # Whether or not to enable instructor email
    email_enabled = models.BooleanField(default=False)

    @classmethod
    def instructor_email_enabled(cls, course_id):
        """
        Returns whether or not email is enabled for the given course id.
        """
        try:
            record = cls.objects.get(course_id=course_id)
            return record.email_enabled
        except cls.DoesNotExist:
            return False

    def __unicode__(self):
        not_en = "Not "
        if self.email_enabled:
            not_en = ""
        # pylint: disable=no-member
        return u"Course '{}': Instructor Email {}Enabled".format(self.course_id.to_deprecated_string(), not_en)


class BulkEmailFlag(ConfigurationModel):
    """
    Enables site-wide configuration for the bulk_email feature.

    Staff can only send bulk email for a course if all the following conditions are true:
    1. BulkEmailFlag is enabled.
    2. Course-specific authorization not required, or course authorized to use bulk email.
    """
    # boolean field 'enabled' inherited from parent ConfigurationModel
    require_course_email_auth = models.BooleanField(default=True)

    @classmethod
    def feature_enabled(cls, course_id=None):
        """
        Looks at the currently active configuration model to determine whether the bulk email feature is available.

        If the flag is not enabled, the feature is not available.
        If the flag is enabled, course-specific authorization is required, and the course_id is either not provided
            or not authorixed, the feature is not available.
        If the flag is enabled, course-specific authorization is required, and the provided course_id is authorized,
            the feature is available.
        If the flag is enabled and course-specific authorization is not required, the feature is available.
        """
        if not BulkEmailFlag.is_enabled():
            return False
        elif BulkEmailFlag.current().require_course_email_auth:
            if course_id is None:
                return False
            else:
                return CourseAuthorization.instructor_email_enabled(course_id)
        else:  # implies enabled == True and require_course_email == False, so email is globally enabled
            return True

    class Meta(object):
        app_label = "bulk_email"

    def __unicode__(self):
        current_model = BulkEmailFlag.current()
        return u"<BulkEmailFlag: enabled {}, require_course_email_auth: {}>".format(
            current_model.is_enabled(),
            current_model.require_course_email_auth
        )
