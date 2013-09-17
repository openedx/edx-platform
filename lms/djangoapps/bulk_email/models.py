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
from django.db import models, transaction
from django.contrib.auth.models import User
from html_to_text import html_to_text

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

    class Meta:  # pylint: disable=C0111
        abstract = True


SEND_TO_MYSELF = 'myself'
SEND_TO_STAFF = 'staff'
SEND_TO_ALL = 'all'
TO_OPTIONS = [SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_ALL]


class CourseEmail(Email, models.Model):
    """
    Stores information for an email to a course.
    """
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
        (SEND_TO_ALL, 'All')
    )
    course_id = models.CharField(max_length=255, db_index=True)
    to_option = models.CharField(max_length=64, choices=TO_OPTION_CHOICES, default=SEND_TO_MYSELF)

    def __unicode__(self):
        return self.subject

    @classmethod
    def create(cls, course_id, sender, to_option, subject, html_message, text_message=None):
        """
        Create an instance of CourseEmail.

        The CourseEmail.save_now method makes sure the CourseEmail entry is committed.
        When called from any view that is wrapped by TransactionMiddleware,
        and thus in a "commit-on-success" transaction, an autocommit buried within here
        will cause any pending transaction to be committed by a successful
        save here.  Any future database operations will take place in a
        separate transaction.
        """
        # automatically generate the stripped version of the text from the HTML markup:
        if text_message is None:
            text_message = html_to_text(html_message)

        # perform some validation here:
        if to_option not in TO_OPTIONS:
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
        )
        course_email.save_now()

        return course_email

    @transaction.autocommit
    def save_now(self):
        """
        Writes InstructorTask immediately, ensuring the transaction is committed.

        Autocommit annotation makes sure the database entry is committed.
        When called from any view that is wrapped by TransactionMiddleware,
        and thus in a "commit-on-success" transaction, this autocommit here
        will cause any pending transaction to be committed by a successful
        save here.  Any future database operations will take place in a
        separate transaction.
        """
        self.save()


class Optout(models.Model):
    """
    Stores users that have opted out of receiving emails from a course.
    """
    # Allowing null=True to support data migration from email->user.
    # We need to first create the 'user' column with some sort of default in order to run the data migration,
    # and given the unique index, 'null' is the best default value.
    user = models.ForeignKey(User, db_index=True, null=True)
    course_id = models.CharField(max_length=255, db_index=True)

    class Meta:  # pylint: disable=C0111
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
    html_template = models.TextField(null=True, blank=True)
    plain_template = models.TextField(null=True, blank=True)

    @staticmethod
    def get_template():
        """
        Fetch the current template

        If one isn't stored, an exception is thrown.
        """
        return CourseEmailTemplate.objects.get()

    @staticmethod
    def _render(format_string, message_body, context):
        """
        Create a text message using a template, message body and context.

        Convert message body (`message_body`) into an email message
        using the provided template.  The template is a format string,
        which is rendered using format() with the provided `context` dict.

        This doesn't insert user's text into template, until such time we can
        support proper error handling due to errors in the message body
        (e.g. due to the use of curly braces).

        Instead, for now, we insert the message body *after* the substitutions
        have been performed, so that anything in the message body that might
        interfere will be innocently returned as-is.

        Output is returned as a unicode string.  It is not encoded as utf-8.
        Such encoding is left to the email code, which will use the value
        of settings.DEFAULT_CHARSET to encode the message.
        """
        # If we wanted to support substitution, we'd call:
        # format_string = format_string.replace(COURSE_EMAIL_MESSAGE_BODY_TAG, message_body)
        result = format_string.format(**context)
        # Note that the body tag in the template will now have been
        # "formatted", so we need to do the same to the tag being
        # searched for.
        message_body_tag = COURSE_EMAIL_MESSAGE_BODY_TAG.format()
        result = result.replace(message_body_tag, message_body, 1)

        # finally, return the result, without converting to an encoded byte array.
        return result

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
