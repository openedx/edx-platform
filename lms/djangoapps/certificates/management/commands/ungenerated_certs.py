from django.utils.simplejson import dumps
from django.core.management.base import BaseCommand, CommandError
from certificates.models import GeneratedCertificate
from courseware import grades, courses
from django.contrib.auth.models import User
from django.test.client import RequestFactory
from profilehooks import profile
import cProfile
from pprint import pprint
from capa.xqueue_interface import XQueueInterface
from capa.xqueue_interface import make_xheader
from django.conf import settings
from requests.auth import HTTPBasicAuth


class Command(BaseCommand):

    help = """
    This command finds all users that have not been graded
    for a single course.
    It returns a json formatted list of users and their user ids
    """

#    @profile
    def _grade(self,student, request, course):
        grades.grade(student, request, course)

    def handle(self, *args, **options):
        factory = RequestFactory()
        course_id = 'BerkeleyX/CS169.1x/2012_Fall'
        course = courses.get_course_by_id(course_id)
        if settings.XQUEUE_INTERFACE.get('basic_auth') is not None:
            requests_auth = HTTPBasicAuth(
                    *settings.XQUEUE_INTERFACE['basic_auth'])
        else:
            requests_auth = None

        xqueue_interface = XQueueInterface(
                settings.XQUEUE_INTERFACE['url'],
                settings.XQUEUE_INTERFACE['django_auth'],
                requests_auth,
                )

        header = make_xheader('/certificate', 'foo', 'test-pull')
        print "Sending test message to queue"
        xqueue_interface.send_to_queue(header, { 'test': 'foo' })

        #enrolled_students = User.objects.filter(
        #        courseenrollment__course_id=course_id).prefetch_related(
        #                "groups").order_by('username')
        #generated_certificates = GeneratedCertificate.objects.filter(
        #        course_id=course_id)
        #request = factory.get('/')
        #student = User.objects.get(username='03199618')
        #print "total students: {0}".format(len(enrolled_students))
        #count = 0
        #for student in enrolled_students:
        #    count += 1
        #    if count % 1000 == 0:
        #        print "{0}/{1}".format(count, len(enrolled_students))
        #    grades.grade(student, request, course)

        #for student in enrolled_students:
        #    g = grades.grade(student, request, course)
        #    if g['grade'] is not None:
        #        print str(student)
        #        pprint(g)
        #        break



