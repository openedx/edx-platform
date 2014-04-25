from certificates.models import GeneratedCertificate
from certificates.models import certificate_status_for_student
from certificates.models import CertificateStatuses as status
from certificates.models import CertificateWhitelist

from courseware import grades, courses
from django.test.client import RequestFactory
from capa.xqueue_interface import XQueueInterface
from capa.xqueue_interface import make_xheader, make_hashkey
from django.conf import settings
from requests.auth import HTTPBasicAuth
from student.models import UserProfile, CourseEnrollment
from verify_student.models import SoftwareSecurePhotoVerification

import json
import random
import logging
from xmodule.modulestore import Location


logger = logging.getLogger(__name__)


class XQueueCertInterface(object):
    """
    XQueueCertificateInterface provides an
    interface to the xqueue server for
    managing student certificates.

    Instantiating an object will create a new
    connection to the queue server.

    See models.py for valid state transitions,
    summary of methods:

       add_cert:   Add a new certificate.  Puts a single
                   request on the queue for the student/course.
                   Once the certificate is generated a post
                   will be made to the update_certificate
                   view which will save the certificate
                   download URL.

       regen_cert: Regenerate an existing certificate.
                   For a user that already has a certificate
                   this will delete the existing one and
                   generate a new cert.


       del_cert:   Delete an existing certificate
                   For a user that already has a certificate
                   this will delete his cert.

    """

    def __init__(self, request=None):

        # Get basic auth (username/password) for
        # xqueue connection if it's in the settings

        if settings.XQUEUE_INTERFACE.get('basic_auth') is not None:
            requests_auth = HTTPBasicAuth(
                *settings.XQUEUE_INTERFACE['basic_auth'])
        else:
            requests_auth = None

        if request is None:
            factory = RequestFactory()
            self.request = factory.get('/')
        else:
            self.request = request

        self.xqueue_interface = XQueueInterface(
            settings.XQUEUE_INTERFACE['url'],
            settings.XQUEUE_INTERFACE['django_auth'],
            requests_auth,
        )
        self.whitelist = CertificateWhitelist.objects.all()
        self.restricted = UserProfile.objects.filter(allow_certificate=False)
        self.use_https = True

    def regen_cert(self, student, course_id, course=None, forced_grade=None, template_file=None):
        """(Re-)Make certificate for a particular student in a particular course

        Arguments:
          student   - User.object
          course_id - courseenrollment.course_id (string)

        WARNING: this command will leave the old certificate, if one exists,
                 laying around in AWS taking up space. If this is a problem,
                 take pains to clean up storage before running this command.

        Change the certificate status to unavailable (if it exists) and request
        grading. Passing grades will put a certificate request on the queue.

        Return the status object.
        """
        # TODO: when del_cert is implemented and plumbed through certificates
        #       repo also, do a deletion followed by a creation r/t a simple
        #       recreation. XXX: this leaves orphan cert files laying around in
        #       AWS. See note in the docstring too.
        try:
            certificate = GeneratedCertificate.objects.get(user=student, course_id=course_id)
            certificate.status = status.unavailable
            certificate.save()
        except GeneratedCertificate.DoesNotExist:
            pass

        return self.add_cert(student, course_id, course, forced_grade, template_file)

    def del_cert(self, student, course_id):

        """
        Arguments:
          student - User.object
          course_id - courseenrollment.course_id (string)

        Removes certificate for a student, will change
        the certificate status to 'deleting'.

        Certificate must be in the 'error' or 'downloadable' state
        otherwise it will return the current state

        """

        raise NotImplementedError

    def add_cert(self, student, course_id, course=None, forced_grade=None, template_file=None, title='None'):
        """
        Request a new certificate for a student.

        Arguments:
          student   - User.object
          course_id - courseenrollment.course_id (CourseKey)
          forced_grade - a string indicating a grade parameter to pass with
                         the certificate request. If this is given, grading
                         will be skipped.

        Will change the certificate status to 'generating'.

        Certificate must be in the 'unavailable', 'error',
        'deleted' or 'generating' state.

        If a student has a passing grade or is in the whitelist
        table for the course a request will be made for a new cert.

        If a student has allow_certificate set to False in the
        userprofile table the status will change to 'restricted'

        If a student does not have a passing grade the status
        will change to status.notpassing

        Returns the student's status
        """

        VALID_STATUSES = [status.generating,
                          status.unavailable,
                          status.deleted,
                          status.error,
                          status.notpassing]

        cert_status = certificate_status_for_student(student, course_id)['status']

        new_status = cert_status

        if cert_status in VALID_STATUSES:
            # grade the student

            # re-use the course passed in optionally so we don't have to re-fetch everything
            # for every student
            if course is None:
                course = courses.get_course_by_id(course_id)
            profile = UserProfile.objects.get(user=student)

            # Needed
            self.request.user = student
            self.request.session = {}

            is_whitelisted = self.whitelist.filter(user=student, course_id=course_id, whitelist=True).exists()
            grade = grades.grade(student, self.request, course)
            enrollment_mode = CourseEnrollment.enrollment_mode_for_user(student, course_id)
            mode_is_verified = (enrollment_mode == GeneratedCertificate.MODES.verified)
            user_is_verified = SoftwareSecurePhotoVerification.user_is_verified(student)
            user_is_reverified = SoftwareSecurePhotoVerification.user_is_reverified_for_all(course_id, student)
            cert_mode = enrollment_mode
            if (mode_is_verified and user_is_verified and user_is_reverified):
                template_pdf = "certificate-template-{id.org}-{id.run}-verified.pdf".format(id=course_id)
            elif (mode_is_verified and not (user_is_verified and user_is_reverified)):
                template_pdf = "certificate-template-{id.org}-{id.run}.pdf".format(id=course_id)
                cert_mode = GeneratedCertificate.MODES.honor
            else:
                # honor code and audit students
                template_pdf = "certificate-template-{id.org}-{id.offering}.pdf".format(id=course_id)
            if forced_grade:
                grade['grade'] = forced_grade

            cert, __ = GeneratedCertificate.objects.get_or_create(user=student, course_id=course_id)

            cert.mode = cert_mode
            cert.user = student
            cert.grade = grade['percent']
            cert.course_id = course_id
            cert.name = profile.name

            if is_whitelisted or grade['grade'] is not None:

                # check to see whether the student is on the
                # the embargoed country restricted list
                # otherwise, put a new certificate request
                # on the queue

                if self.restricted.filter(user=student).exists():
                    new_status = status.restricted
                    cert.status = new_status
                    cert.save()
                else:
                    key = make_hashkey(random.random())
                    cert.key = key
                    contents = {
                        'action': 'create',
                        'username': student.username,
                        'course_id': course_id.to_deprecated_string(),
                        'name': profile.name,
                        'grade': grade['grade'],
                        'template_pdf': template_pdf,
                    }
                    if template_file:
                        contents['template_pdf'] = template_file
                    new_status = status.generating
                    cert.status = new_status
                    cert.save()
                    self._send_to_xqueue(contents, key)
            else:
                new_status = status.notpassing
                cert.status = new_status
                cert.save()

        return new_status

    def _send_to_xqueue(self, contents, key):

        if self.use_https:
            proto = "https"
        else:
            proto = "http"

        xheader = make_xheader(
            '{0}://{1}/update_certificate?{2}'.format(
                proto, settings.SITE_NAME, key), key, settings.CERT_QUEUE)

        (error, msg) = self.xqueue_interface.send_to_queue(
            header=xheader, body=json.dumps(contents))
        if error:
            logger.critical('Unable to add a request to the queue: {} {}'.format(error, msg))
            raise Exception('Unable to send queue message')
