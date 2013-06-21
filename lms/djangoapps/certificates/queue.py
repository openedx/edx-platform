from certificates.models import GeneratedCertificate
from certificates.models import certificate_status_for_student
from certificates.models import CertificateStatuses as status
from certificates.models import CertificateWhitelist

from mitxmako.middleware import MakoMiddleware
from courseware import grades, courses
from django.test.client import RequestFactory
from capa.xqueue_interface import XQueueInterface
from capa.xqueue_interface import make_xheader, make_hashkey
from django.conf import settings
from requests.auth import HTTPBasicAuth
from student.models import UserProfile

import json
import random
import logging


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
        # MakoMiddleware Note:
        # Line below has the side-effect of writing to a module level lookup
        # table that will allow problems to render themselves. If this is not
        # present, problems that a student hasn't seen will error when loading,
        # causing the grading system to under-count the possible score and
        # inflate their grade. This dependency is bad and was probably recently
        # introduced. This is the bandage until we can trace the root cause.
        m = MakoMiddleware()

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

    def regen_cert(self, student, course_id):
        """
        Arguments:
          student - User.object
          course_id - courseenrollment.course_id (string)

        Removes certificate for a student, will change
        the certificate status to 'regenerating'.

        Certificate must be in the 'error' or 'downloadable' state

        If the student has a passing grade a certificate
        request will be put on the queue

        If the student is not passing his state will change
        to status.notpassing

        otherwise it will return the current state

        """

        raise NotImplementedError

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

    def add_cert(self, student, course_id, course=None):
        """

        Arguments:
          student - User.object
          course_id - courseenrollment.course_id (string)

        Request a new certificate for a student.
        Will change the certificate status to 'generating'.

        Certificate must be in the 'unavailable', 'error',
        'deleted' or 'generating' state.

        If a student has a passing grade or is in the whitelist
        table for the course a request will made for a new cert.

        If a student has allow_certificate set to False in the
        userprofile table the status will change to 'restricted'


        If a student does not have a passing grade the status
        will change to status.notpassing

        Returns the student's status

        """

        VALID_STATUSES = [status.generating,
                status.unavailable, status.deleted, status.error,
                status.notpassing]

        cert_status = certificate_status_for_student(
                              student, course_id)['status']

        if cert_status in VALID_STATUSES:
            # grade the student

            # re-use the course passed in optionally so we don't have to re-fetch everything
            # for every student
            if course is None:
                course = courses.get_course_by_id(course_id)
            profile = UserProfile.objects.get(user=student)

            cert, created = GeneratedCertificate.objects.get_or_create(
                   user=student, course_id=course_id)

            # Needed
            self.request.user = student
            self.request.session = {}

            grade = grades.grade(student, self.request, course)
            is_whitelisted = self.whitelist.filter(
                user=student, course_id=course_id, whitelist=True).exists()

            if is_whitelisted or grade['grade'] is not None:

                key = make_hashkey(random.random())

                cert.grade = grade['percent']
                cert.user = student
                cert.course_id = course_id
                cert.key = key
                cert.name = profile.name

                # check to see whether the student is on the
                # the embargoed country restricted list
                # otherwise, put a new certificate request
                # on the queue
                if self.restricted.filter(user=student).exists():
                    cert.status = status.restricted
                else:
                    contents = {
                        'action': 'create',
                        'username': student.username,
                        'course_id': course_id,
                        'name': profile.name,
                    }
                    cert.status = status.generating
                    self._send_to_xqueue(contents, key)
                cert.save()
            else:
                cert_status = status.notpassing
                cert.grade = grade['percent']
                cert.status = cert_status
                cert.user = student
                cert.course_id = course_id
                cert.name = profile.name
                cert.save()

        return cert_status

    def _send_to_xqueue(self, contents, key):

        xheader = make_xheader(
            'https://{0}/update_certificate?{1}'.format(
                settings.SITE_NAME, key), key, settings.CERT_QUEUE)

        (error, msg) = self.xqueue_interface.send_to_queue(
                header=xheader, body=json.dumps(contents))
        if error:
            logger.critical('Unable to add a request to the queue: {} {}'.format(error, msg))
            raise Exception('Unable to send queue message')
