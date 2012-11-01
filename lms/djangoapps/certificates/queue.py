from django.utils.simplejson import dumps
from django.core.management.base import BaseCommand, CommandError
from certificates.models import GeneratedCertificate
from certificates.models import certificate_status_for_student
from courseware import grades, courses
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from pprint import pprint
from capa.xqueue_interface import XQueueInterface
from capa.xqueue_interface import make_xheader, make_hashkey
from django.conf import settings
from requests.auth import HTTPBasicAuth
from student.models import UserProfile
import json
import random
import logging


def add_cert_to_queue(student, course_id, xqueue_interface, request=None):
    """
    Update or create a new GeneratedCertificates:
      
    If certificate generation is in progress this function will
    return None. 

    If certificate generation was completed for the user this
    will add a request to delete the existing certificate.

    A new certificate request will be made if the student's
    grade is not None
    """
    log = logging.getLogger("mitx.certificates")
    if request is None:
        factory = RequestFactory()
        request = factory.get('/')

    cert_status = certificate_status_for_student(student, course_id)
    if cert_status['status'] == 'generating':
        return None

    if cert_status['status'] == 'downloadable':
        generated_certificate = GeneratedCertificate.objects.get(
            user=student, course_id=course_id)
        generated_certificate.status = 'unavailable'
        key = generated_certificate.key
        username = generated_certificate.user.username
        generated_certificate.save()

        contents = {
             'remove': True,
             'verify_uuid': cert.verify_uuid,
             'download_uuid': cert.download_uuid,
             'key': cert.key,
             'username': cert.user.username
        }
        xheader = make_xheader('http://sandbox-jrjarvis-001.m.edx.org/certificate', key, 'test-pull')
        (error, msg) = xqueue_interface.send_to_queue(header=xheader,
                             body=json.dumps(contents))

    # grade the student
    course = courses.get_course_by_id(course_id)
    grade = grades.grade(student, request, course)

    if grade['grade'] is not None:
        cert, created = GeneratedCertificate.objects.get_or_create(
               user=student, course_id=course_id)
        profile = UserProfile.objects.get(user=student)

        key = make_hashkey(random.random())

        cert.status = 'generating' 
        cert.grade = grade['percent']
        cert.user = student
        cert.course_id = course_id
        cert.key = key
        cert.save()

        contents = {
            'username': student.username,
            'course_id': course_id,
            'name': profile.name,
        }
        xheader = make_xheader('http://sandbox-jrjarvis-001.m.edx.org/update_certificate', key, 'test-pull')
        (error, msg) = xqueue_interface.send_to_queue(header=xheader,
                             body=json.dumps(contents))
        if error:
            log.critical('Unable to send message')

