from django.core.management.base import BaseCommand
from certificates.models import certificate_status_for_student
from certificates.queue import XQueueCertInterface
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = """
    Find all students that have need certificates
    and put certificate requests on the queue

    This is only for BerkeleyX/CS169.1x/2012_Fall
    """

    def handle(self, *args, **options):

        # TODO This is only temporary for CS169 certs

        course_id = 'BerkeleyX/CS169.1x/2012_Fall'
        enrolled_students = User.objects.filter(
                courseenrollment__course_id=course_id).prefetch_related(
                        "groups").order_by('username')
        xq = XQueueCertInterface()
        for student in enrolled_students:
            if certificate_status_for_student(
                     student, course_id)['status'] == 'unavailable':
                ret = xq.add_cert(student, course_id)
                if ret == 'generating':
                    print 'generating for {0}'.format(student)
