# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from certificates.models import certificate_status_for_student
from certificates.queue import XQueueCertInterface
from django.contrib.auth.models import User
from student.models import UserProfile


class Command(BaseCommand):

    help = """
    Looks for names that have unicode characters
    and queues them up for a certificate request
    """

    def handle(self, *args, **options):

        # TODO this is only temporary for CS169 certs

        course_id = 'BerkeleyX/CS169.1x/2012_Fall'

        enrolled_students = User.objects.filter(
                courseenrollment__course_id=course_id).prefetch_related(
                        "groups").order_by('username')
        xq = XQueueCertInterface()
        print "Looking for unusual names.."
        for student in enrolled_students:
            if certificate_status_for_student(
                     student, course_id)['status'] == 'unavailable':
                continue
            name = UserProfile.objects.get(user=student).name
            for c in name:
                if ord(c) >= 0x200:
                    ret = xq.add_cert(student, course_id)
                    if ret == 'generating':
                        print 'generating for {0}'.format(student)
                    break
