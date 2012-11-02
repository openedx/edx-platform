from django.core.management.base import BaseCommand
from certificates.models import GeneratedCertificate
from certificates.queue import XQueueCertInterface
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = """
    Find all students that have need certificates
    and put certificate requests on the queue
    """

    def handle(self, *args, **options):

        course_id = 'BerkeleyX/CS169.1x/2012_Fall'

        enrolled_students = User.objects.filter(
                courseenrollment__course_id=course_id).prefetch_related(
                        "groups").order_by('username')
        xq = XQueueCertInterface()

        # TODO (this is for debugging, remove)
        for c in GeneratedCertificate.objects.all():
            c.delete()

        count = 0
        for student in enrolled_students:
            ret = xq.add_cert(student, course_id)
            if ret == 'generating':
                print 'generating for {0}'.format(student)
                count += 1
            if count > 10:
                break
