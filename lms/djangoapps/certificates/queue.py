from certificates.models import GeneratedCertificate
from certificates.models import certificate_status_for_student
from certificates.models import CertificateStatuses as status

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

    def regen_cert(self, student, course_id):
        """

        Arguments:
          student - User.object
          course_id - courseenrollment.course_id (string)

        Removes certificate for a student, will change
        the certificate status to 'regenerating'.
        Will invalidate the old certificate and generate
        a new one.

        When completed the certificate status will change
        to 'downloadable'

        Returns the certificate status.

        """

        VALID_STATUSES = [status.downloadable]

        cert_status = certificate_status_for_student(
                              student, course_id)['status']

        if cert_status in VALID_STATUSES:

            profile = UserProfile.objects.get(user=student)

            cert = GeneratedCertificate.objects.get(
                user=student, course_id=course_id)
            cert.status = status.regenerating
            cert.save()

            contents = {
                 'action': 'regen',
                 'remove_verify_uuid': cert.verify_uuid,
                 'remove_download_uuid': cert.download_uuid,
                 'username': cert.user.username,
                 'course_id': cert.course_id,
                 'name': profile.name,
                }

            key = cert.key
            xheader = make_xheader(
                    'http://{0}/certificate'.format(settings.SITE_NAME),
                    key, 'test-pull')
            (error, msg) = self.xqueue_interface.send_to_queue(
                    header=xheader, body=json.dumps(contents))
            if error:
                logger.critical('Unable to add a request to the queue')
                raise Exception('Unable to send queue message')

        return cert_status

    def remove_cert(self, student, course_id):
        """

        Arguments:
          student - User.object
          course_id - courseenrollment.course_id (string)

        Removes certificate for a student, will change
        the certificate status to 'deleting'.

        When completed the certificate status will change
        to 'deleted'.

        Returns the certificate status.

        """

        VALID_STATUSES = [status.downloadable]

        cert_status = certificate_status_for_student(
                              student, course_id)['status']

        if cert_status in VALID_STATUSES:

            cert = GeneratedCertificate.objects.get(
                user=student, course_id=course_id)
            cert.status = status.deleting
            cert.save()

            contents = {
                 'action': 'remove',
                 'remove_verify_uuid': cert.verify_uuid,
                 'remove_download_uuid': cert.download_uuid,
                 'username': cert.user.username,
            }

            key = cert.key
            xheader = make_xheader(
                    'http://{0}/certificate'.format(settings.SITE_NAME),
                    key, 'test-pull')
            (error, msg) = self.xqueue_interface.send_to_queue(header=xheader,
                                 body=json.dumps(contents))

        return cert_status

    def add_cert_to_queue(self, student, course_id):
        """

        Arguments:
          student - User.object
          course_id - courseenrollment.course_id (string)

        Adds a new certificate request to the queue only if
        the current certificate status is 'unavailable' or
        'deleted' and the student has a passing grade for
        the course.

        When completed the certificate status will change
        to 'downloadable'.

        If the current status is 'generating', 'regenerating'
        or 'deleting' this function will return that status

        Returns 'unavailable' if the student is eligible for
        a certificate but does not have a passing grade.

        """

        VALID_STATUSES = [status.unavailable, status.deleted]

        cert_status = certificate_status_for_student(
                              student, course_id)['status']

        if cert_status in VALID_STATUSES:
            # grade the student
            course = courses.get_course_by_id(course_id)
            grade = grades.grade(student, self.request, course)

            if grade['grade'] is not None:
                cert_status = status.generating
                cert, created = GeneratedCertificate.objects.get_or_create(
                       user=student, course_id=course_id)
                profile = UserProfile.objects.get(user=student)

                key = make_hashkey(random.random())
                cert.status = cert_status
                cert.grade = grade['percent']
                cert.user = student
                cert.course_id = course_id
                cert.key = key
                cert.save()

                contents = {
                    'action': 'create',
                    'username': student.username,
                    'course_id': course_id,
                    'name': profile.name,
                }
                xheader = make_xheader(
                    'http://{0}/update_certificate?{1}'.format(
                        key, settings.SITE_NAME), key, 'test-pull')

                (error, msg) = self.xqueue_interface.send_to_queue(
                                  header=xheader, body=json.dumps(contents))
                if error:
                    logger.critical('Unable to post results to qserver')
                    raise Exception('Unable to send queue message')

        return cert_status
