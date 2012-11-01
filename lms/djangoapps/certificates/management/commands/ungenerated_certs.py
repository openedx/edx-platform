from django.utils.simplejson import dumps
from django.core.management.base import BaseCommand, CommandError
from certificates.models import GeneratedCertificate
from certificates.models import certificate_status_for_student
from certificates.queue import XQueueCertInterface
from courseware import grades, courses
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from capa.xqueue_interface import XQueueInterface
from capa.xqueue_interface import make_xheader, make_hashkey
from django.conf import settings
from requests.auth import HTTPBasicAuth
from student.models import UserProfile
import json
import random
import logging


class Command(BaseCommand):

    help = """
    Find all students that have need certificates
    and put certificate requests on the queue
    """

    def handle(self, *args, **options):

        course_id = 'BerkeleyX/CS169.1x/2012_Fall'
        course = courses.get_course_by_id(course_id)

        enrolled_students = User.objects.filter(
                courseenrollment__course_id=course_id).prefetch_related(
                        "groups").order_by('username')
        xq = XQueueCertInterface()
        # delete all entries
        for c in GeneratedCertificate.objects.all():
            c.delete()

        count = 0
        for student in enrolled_students:
            ret = xq.add_cert_to_queue(student, course_id)
            if ret == 'generating':
                print 'generating for {0}'.format(student)
                count += 1
            if count > 10:
                break
