from django.core.management.base import BaseCommand
from certificates.models import certificate_status_for_student
from django.contrib.auth.models import User
from optparse import make_option
from django.conf import settings
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from collections import Counter


class Command(BaseCommand):

    help = """

    Generate a certificate status report for all courses that have ended.
    This command does not do anything other than report the current
    certificate status.

    unavailable  - A student is not eligible for a certificate.
    generating   - A request has been made to generate a certificate,
                   but it has not been generated yet.
    regenerating - A request has been made to regenerate a certificate,
                   but it has not been generated yet.
    deleting     - A request has been made to delete a certificate.

    deleted      - The certificate has been deleted.
    downloadable - The certificate is available for download.
    notpassing   - The student was graded but is not passing

    """

    option_list = BaseCommand.option_list + (
        make_option('-c', '--course',
            metavar='COURSE_ID',
            dest='course',
            default=None,
            help='Only generate for COURSE_ID'),
        )

    def handle(self, *args, **options):

        # Find all courses that have ended

        if options['course']:
            ended_courses = [options['course']]
        else:
            ended_courses = []
            for course_id in [course  # all courses in COURSE_LISTINGS
                    for sub in settings.COURSE_LISTINGS
                        for course in settings.COURSE_LISTINGS[sub]]:

                course_loc = CourseDescriptor.id_to_location(course_id)
                course = modulestore().get_instance(course_id, course_loc)
                if course.has_ended():
                    ended_courses.append(course_id)

        total_enrolled = {}
        cert_statuses = {}

        for course_id in ended_courses:

            # find students who are enrolled
            print "Looking up certificate states for {0}".format(course_id)
            enrolled_students = User.objects.filter(
                    courseenrollment__course_id=course_id).prefetch_related(
                            "groups").order_by('username')
            total_enrolled[course_id] = enrolled_students.count()

            # tally up certificate statuses for every student
            # enrolled in the course
            cert_statuses[course_id] = Counter(
                    [certificate_status_for_student(
                        student, course_id)['status']
                            for student in enrolled_students])

        # all states we have seen far all courses
        status_headings = set(
                [status for course in cert_statuses
                    for status in cert_statuses[course]])

        # print the heading for the report
        print "{0:>20}{1:>10}".format("course ID", "enrolled"),
        print ' '.join(["{:>12}".format(heading)
                            for heading in status_headings])

        # print the report
        for course_id in total_enrolled:
            print "{0:>20}{1:>10}".format(
                    course_id[0:18], total_enrolled[course_id]),
            for heading in status_headings:
                if heading in cert_statuses[course_id]:
                    print "{:>12}".format(cert_statuses[course_id][heading]),
                else:
                    print " " * 12,
            print
