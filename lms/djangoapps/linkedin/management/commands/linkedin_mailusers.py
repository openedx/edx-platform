"""
Send emails to users inviting them to add their course certificates to their
LinkedIn profiles.
"""

import json
import urllib

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template import Context
from django.template.loader import get_template
from django.core.urlresolvers import reverse
from optparse import make_option

from edxmako.shortcuts import render_to_string

from certificates.models import GeneratedCertificate
from courseware.courses import get_course_by_id, course_image_url

from ...models import LinkedIn
from . import LinkedInAPI


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
            '--grandfather',
            action='store_true',
            dest='grandfather',
            default=False,
            help="Creates aggregate invitations for all certificates a user "
                 "has earned to date and sends a 'grandfather' email.  This is "
                 "intended to be used when the feature is launched to invite "
                 "all users that have earned certificates to date to add their "
                 "certificates.  Afterwards the default, one email per "
                 "certificate mail form will be used."),)

    def __init__(self):
        super(Command, self).__init__()
        self.api = LinkedInAPI(self)

    def handle(self, *args, **options):
        whitelist = self.api.config.get('EMAIL_WHITELIST')
        grandfather = options.get('grandfather', False)
        accounts = LinkedIn.objects.filter(has_linkedin_account=True)
        for account in accounts:
            user = account.user
            if whitelist is not None and user.email not in whitelist:
                # Whitelist only certain addresses for testing purposes
                continue
            emailed = json.loads(account.emailed_courses)
            certificates = GeneratedCertificate.objects.filter(user=user)
            certificates = certificates.filter(status='downloadable')
            certificates = [cert for cert in certificates
                            if cert.course_id not in emailed]
            if not certificates:
                continue
            if grandfather:
                self.send_grandfather_email(user, certificates)
                emailed.extend([cert.course_id for cert in certificates])
            else:
                for certificate in certificates:
                    self.send_triggered_email(user, certificate)
                    emailed.append(certificate.course_id)
            account.emailed_courses = json.dumps(emailed)
            account.save()

    def certificate_url(self, certificate, grandfather=False):
        """
        Generates a certificate URL based on LinkedIn's documentation.  The
        documentation is from a Word document: DAT_DOCUMENTATION_v3.12.docx
        """
        course = get_course_by_id(certificate.course_id)
        tracking_code = '-'.join([
            'eml',
            'prof',  # the 'product'--no idea what that's supposed to mean
            course.org,  # Partner's name
            course.number,  # Certificate's name
            'gf' if grandfather else 'T'])
        query = [
            ('pfCertificationName', certificate.name),
            ('pfAuthorityName', settings.PLATFORM_NAME),
            ('pfAuthorityId', self.api.config['COMPANY_ID']),
            ('pfCertificationUrl', certificate.download_url),
            ('pfLicenseNo', certificate.course_id),
            ('pfCertStartDate', course.start.strftime('%Y%m')),
            ('_mSplash', '1'),
            ('trk', tracking_code),
            ('startTask', 'CERTIFICATION_NAME'),
            ('force', 'true')]
        return 'http://www.linkedin.com/profile/guided?' + urllib.urlencode(query)

    def send_grandfather_email(self, user, certificates):
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

            course_title = course.display_name

            course_img_url = 'https://{}{}'.format(settings.SITE_NAME, course_image_url(course))
            course_end_date = course.end.strftime('%b %Y')
            course_org = course.display_organization

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
        subject = 'Congratulations! Put your certificates on LinkedIn'
        self.send_email(user, subject, body)

    def send_triggered_email(self, user, certificate):
        """
        Email a user that recently earned a certificate, inviting them to post
        their certificate on their LinkedIn profile.
        """
        template = get_template("linkedin_email.html")
        url = self.certificate_url(certificate)
        context = Context({
            'student_name': user.profile.name,
            'course_name': certificate.name,
            'url': url})
        body = template.render(context)
        subject = 'Congratulations! Put your certificate on LinkedIn'
        self.send_email(user, subject, body)

    def send_email(self, user, subject, body):
        """
        Send an email.
        """
        fromaddr = settings.DEFAULT_FROM_EMAIL
        toaddr = '%s <%s>' % (user.profile.name, user.email)
        send_mail(subject, body, fromaddr, (toaddr,))
