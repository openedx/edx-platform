import logging
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.conf import settings
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
import os

import boto3

logger = logging.getLogger(__name__)


def calendar_sync_initial_email_content(course_name):
    subject = _('Stay on Track')
    body_text = _('Sticking to a schedule is the best way to ensure that you successfully complete your self-paced '
                  'course. This schedule of assignment due dates for {course} will help you stay on track!'
                  ).format(course=course_name)
    body = format_html('<div>{text}</div>', text=body_text)
    return subject, body


def calendar_sync_update_email_content(course_name):
    subject = _('Updates for Your {course} Schedule').format(course=course_name)
    body_text = _('Your assignment due dates for {course} were recently adjusted. Update your calendar with your new '
                  'schedule to ensure that you stay on track!').format(course=course_name)
    body = format_html('<div>{text}</div>', text=body_text)
    return subject, body


def prepare_attachments(attachment_data):
    """
    Helper function to create a list contain file attachment objects
    for use with MIMEMultipart
    Returns a list of MIMEApplication objects
    """

    attachments = []
    for filename, data in attachment_data.items():
        msg_attachment = MIMEApplication(data)
        msg_attachment.add_header(
            'Content-Disposition',
            'attachment',
            filename=os.path.basename(filename)
        )
        msg_attachment.set_type('text/calendar')
        attachments.append(msg_attachment)

    return attachments


def send_email_with_attachment(to_emails, attachment_data, course_name, is_update=False):
    # connect to SES
    client = boto3.client('ses', region_name=settings.AWS_SES_REGION_NAME)

    subject, body = (calendar_sync_update_email_content(course_name) if is_update else
                     calendar_sync_initial_email_content(course_name))

    # build email body as html
    msg_body = MIMEText(body, 'html')

    attachments = prepare_attachments(attachment_data)

    # iterate over each email in the list to send emails independently
    for email in to_emails:
        msg = MIMEMultipart()
        msg['Subject'] = str(subject)
        msg['From'] = settings.BULK_EMAIL_DEFAULT_FROM_EMAIL
        msg['To'] = email

        # attach the message body and attachment
        msg.attach(msg_body)
        for msg_attachment in attachments:
            msg.attach(msg_attachment)

        # send the email
        result = client.send_raw_email(Source=msg['From'], Destinations=[email], RawMessage={'Data': msg.as_string()})
        logger.debug(result)
