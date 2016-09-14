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
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction

from openedx.core.lib.html_to_text import html_to_text
from openedx.core.lib.mail_utils import wrap_message

from instructor_email_widget.models import GroupedQuery
from xmodule_django.models import CourseKeyField
from util.keyword_substitution import substitute_keywords_with_data

log = logging.getLogger(__name__)

# Bulk email to_options - the send to options that users can
# select from when they send email.
SEND_TO_MYSELF = 'myself'
SEND_TO_STAFF = 'staff'
SEND_TO_ALL = 'all'
TO_OPTIONS = [SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_ALL]


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


class CourseEmail(Email):
    """
    Stores information for an email to a course.
    """
    class Meta(object):
        app_label = "bulk_email"

    # Three options for sending that we provide from the instructor dashboard:
    # * Myself: This sends an email to the staff member that is composing the email.
    #
    # * Staff and instructors: This sends an email to anyone in the staff group and
    #   anyone in the instructor group
    #
    # * All: This sends an email to anyone enrolled in the course, with any role
    #   (student, staff, or instructor)
    #
    TO_OPTION_CHOICES = (
        (SEND_TO_MYSELF, 'Myself'),
        (SEND_TO_STAFF, 'Staff and instructors'),
        (SEND_TO_ALL, 'All (students, staff and instructors)'),
    )
    course_id = CourseKeyField(max_length=255, db_index=True)
    to_option = models.CharField(max_length=64, choices=TO_OPTION_CHOICES, default=SEND_TO_MYSELF)
    template_name = models.CharField(null=True, max_length=255)
    from_addr = models.CharField(null=True, max_length=255)

    def __unicode__(self):
        return self.subject

    @classmethod
    def create(
            cls, course_id, sender, to_option, subject, html_message,
            text_message=None, template_name=None, from_addr=None):
        """
        Create an instance of CourseEmail.
        """
        # automatically generate the stripped version of the text from the HTML markup:
        if text_message is None:
            text_message = html_to_text(html_message)

        # perform some validation here:
        if to_option.isdigit():
            if not GroupedQuery.objects.filter(id=int(to_option)).exists():
                message = "Course email for '{course}' being sent to query id that does not exist: {query_id}, subject '{subject}'".format(
                    course=course_id,
                    query_id=to_option,
                    subject=subject,
                )
                raise ValueError(message)
        elif to_option not in TO_OPTIONS:
            fmt = 'Course email being sent to unrecognized to_option: "{to_option}" for "{course}", subject "{subject}"'
            msg = fmt.format(to_option=to_option, course=course_id, subject=subject)
            raise ValueError(msg)

        # create the task, then save it immediately:
        course_email = cls(
            course_id=course_id,
            sender=sender,
            to_option=to_option,
            subject=subject,
            html_message=html_message,
            text_message=text_message,
            template_name=template_name,
            from_addr=from_addr,
        )
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
        body are subtituted with user data before the body is inserted into
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

        If email has not been explicitly enabled, returns False.
        """
        # If settings.FEATURES['REQUIRE_COURSE_EMAIL_AUTH'] is
        # set to False, then we enable email for every course.
        if not settings.FEATURES['REQUIRE_COURSE_EMAIL_AUTH']:
            return True

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
