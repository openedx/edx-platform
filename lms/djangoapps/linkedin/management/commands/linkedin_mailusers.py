"""
Send emails to users inviting them to add their course certificates to their
LinkedIn profiles.
"""

from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError, SMTPException
import json
import logging
import urllib

from boto.exception import AWSConnectionError
from boto.ses.exceptions import (
    SESAddressNotVerifiedError,
    SESIdentityNotVerifiedError,
    SESDomainNotConfirmedError,
    SESAddressBlacklistedError,
    SESDailyQuotaExceededError,
    SESMaxSendingRateExceededError,
    SESDomainEndsWithDotError,
    SESLocalAddressCharacterError,
    SESIllegalAddressError,
)
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.db import transaction
from django.template import Context
from django.template.loader import get_template
from django.core.urlresolvers import reverse
from optparse import make_option

from edxmako.shortcuts import render_to_string

from certificates.models import GeneratedCertificate
from courseware.courses import get_course_by_id, course_image_url

from ...models import LinkedIn

# The following is blatantly cribbed from bulk_email/tasks.py

# Errors that an individual email is failing to be sent, and should just
# be treated as a fail.
SINGLE_EMAIL_FAILURE_ERRORS = (
    SESAddressBlacklistedError,  # Recipient's email address has been temporarily blacklisted.
    SESDomainEndsWithDotError,  # Recipient's email address' domain ends with a period/dot.
    SESIllegalAddressError,  # Raised when an illegal address is encountered.
    SESLocalAddressCharacterError,  # An address contained a control or whitespace character.
)

# Exceptions that, if caught, should cause the task to be re-tried.
# These errors will be caught a limited number of times before the task fails.
LIMITED_RETRY_ERRORS = (
    SMTPConnectError,
    SMTPServerDisconnected,
    AWSConnectionError,
)

# Errors that indicate that a mailing task should be retried without limit.
# An example is if email is being sent too quickly, but may succeed if sent
# more slowly.  When caught by a task, it triggers an exponential backoff and retry.
# Retries happen continuously until the email is sent.
# Note that the SMTPDataErrors here are only those within the 4xx range.
# Those not in this range (i.e. in the 5xx range) are treated as hard failures
# and thus like SINGLE_EMAIL_FAILURE_ERRORS.
INFINITE_RETRY_ERRORS = (
    SESMaxSendingRateExceededError,  # Your account's requests/second limit has been exceeded.
    SMTPDataError,
)

# Errors that are known to indicate an inability to send any more emails,
# and should therefore not be retried.  For example, exceeding a quota for emails.
# Also, any SMTP errors that are not explicitly enumerated above.
BULK_EMAIL_FAILURE_ERRORS = (
    SESAddressNotVerifiedError,  # Raised when a "Reply-To" address has not been validated in SES yet.
    SESIdentityNotVerifiedError,  # Raised when an identity has not been verified in SES yet.
    SESDomainNotConfirmedError,  # Raised when domain ownership is not confirmed for DKIM.
    SESDailyQuotaExceededError,  # 24-hour allotment of outbound email has been exceeded.
    SMTPException,
)



MAX_ATTEMPTS = 10

log = logging.getLogger("linkedin")

class Command(BaseCommand):
    """
    Django command for inviting users to add their course certificates to their
    LinkedIn profiles.
    """
    args = ''
    help = ('Sends emails to edX users that are on LinkedIn who have completed '
            'course certificates, inviting them to add their certificates to '
            'their LinkedIn profiles')
    option_list = BaseCommand.option_list + (
        make_option(
            '--mock',
            action='store_true',
            dest='mock_run',
            default=False,
            help="Run without sending the final e-mails."),)

    def __init__(self):
        super(Command, self).__init__()

    @transaction.commit_manually
    def handle(self, *args, **options):
        whitelist = settings.LINKEDIN_API['EMAIL_WHITELIST']
        mock_run = options.get('mock_run', False)
        accounts = LinkedIn.objects.filter(has_linkedin_account=True)

        for account in accounts:
            user = account.user
            if whitelist and user.email not in whitelist:
                # Whitelist only certain addresses for testing purposes
                continue

            try:
                emailed = json.loads(account.emailed_courses)
            except Exception:
                log.exception("LinkedIn: Could not parse emailed_courses for {}".format(user.username))
                continue

            certificates = GeneratedCertificate.objects.filter(user=user)
            certificates = certificates.filter(status='downloadable')
            certificates = [cert for cert in certificates if cert.course_id not in emailed]

            # Shouldn't happen, since we're only picking users who have
            # certificates, but just in case...
            if not certificates:
                log.info("LinkedIn: No certificates for user {}".format(user.username))
                continue

            # Basic sanity checks passed, now try to send the emails
            try:
                success = False
                success = self.send_grandfather_email(user, certificates, mock_run)
                log.info("LinkedIn: Sent email for user {}".format(user.username))
                if not mock_run:
                    emailed.extend([cert.course_id for cert in certificates])
                if success and not mock_run:
                    account.emailed_courses = json.dumps(emailed)
                    account.save()
                    transaction.commit()
            except BULK_EMAIL_FAILURE_ERRORS:
                log.exception("LinkedIn: No further email sending will work, aborting")
                transaction.commit()
                return -1
            except Exception:
                log.exception("LinkedIn: User {} couldn't be processed".format(user.username))

        transaction.commit()


    def certificate_url(self, certificate):
        """
        Generates a certificate URL based on LinkedIn's documentation.  The
        documentation is from a Word document: DAT_DOCUMENTATION_v3.12.docx
        """
        course = get_course_by_id(certificate.course_id)
        tracking_code = '-'.join([
            'eml',
            'prof',  # the 'product'--no idea what that's supposed to mean
            'edX',  # Partner's name
            course.number,  # Certificate's name
            'gf'])
        query = [
            ('pfCertificationName', course.display_name_with_default),
            ('pfAuthorityName', settings.PLATFORM_NAME),
            ('pfAuthorityId', settings.LINKEDIN_API['COMPANY_ID']),
            ('pfCertificationUrl', certificate.download_url),
            ('pfLicenseNo', certificate.course_id),
            ('pfCertStartDate', course.start.strftime('%Y%m')),
            ('_mSplash', '1'),
            ('trk', tracking_code),
            ('startTask', 'CERTIFICATION_NAME'),
            ('force', 'true')]
        return 'http://www.linkedin.com/profile/guided?' + urllib.urlencode(query)

    def send_grandfather_email(self, user, certificates, mock_run=False):
        """
        Send the 'grandfathered' email informing historical students that they
        may now post their certificates on their LinkedIn profiles.
        """
        courses_list = []
        for cert in certificates:
            course = get_course_by_id(cert.course_id)
            course_url = 'https://{}{}'.format(
                settings.SITE_NAME,
                reverse('course_root', kwargs={'course_id': cert.course_id})
            )

            course_title = course.display_name_with_default

            course_img_url = 'https://{}{}'.format(settings.SITE_NAME, course_image_url(course))
            course_end_date = course.end.strftime('%b %Y')
            course_org = course.org

            courses_list.append({
                'course_url': course_url,
                'course_org': course_org,
                'course_title': course_title,
                'course_image_url': course_img_url,
                'course_end_date': course_end_date,
                'linkedin_add_url': self.certificate_url(cert),
            })

        context = {'courses_list': courses_list, 'num_courses': len(courses_list)}
        body = render_to_string('linkedin/linkedin_email.html', context)
        subject = u'{}, Add your Achievements to your LinkedIn Profile'.format(user.profile.name)
        if mock_run:
            return True
        else:
            return self.send_email(user, subject, body)

    def send_email(self, user, subject, body, num_attempts=MAX_ATTEMPTS):
        """
        Send an email. Return True if it succeeded, False if it didn't.
        """
        fromaddr = settings.DEFAULT_FROM_EMAIL
        toaddr = u'{} <{}>'.format(user.profile.name, user.email)
        msg = EmailMessage(subject, body, fromaddr, (toaddr,))
        msg.content_subtype = "html"

        i = 1
        while i <= num_attempts:
            try:
                msg.send()
                return True # Happy path!
            except SINGLE_EMAIL_FAILURE_ERRORS:
                # Something unrecoverable is wrong about the email acct we're sending to
                log.exception(
                    u"LinkedIn: Email send failed for user {}, email {}"
                    .format(user.username, user.email)
                )
                return False
            except LIMITED_RETRY_ERRORS:
                # Something went wrong (probably an intermittent connection error),
                # but maybe if we beat our heads against the wall enough times,
                # we can crack our way through. Thwack! Thwack! Thwack!
                # Give up after num_attempts though (for loop exits), let's not
                # get carried away.
                log.exception(
                    u"LinkedIn: Email send for user {}, email {}, encountered error, attempt #{}"
                    .format(user.username, user.email, i)
                )
                i += 1
                continue
            except INFINITE_RETRY_ERRORS:
                # Dude, it will *totally* work if I just... sleep... a little...
                # Things like max send rate exceeded. The smart thing would be
                # to do exponential backoff. The lazy thing to do would be just
                # sleep some arbitrary amount and trust that it'll probably work.
                # GUESS WHAT WE'RE DOING BOYS AND GIRLS!?!
                log.exception("LinkedIn: temporary error encountered, retrying")
                time.sleep(1)

        # If we hit here, we went through all our attempts without success
        return False
