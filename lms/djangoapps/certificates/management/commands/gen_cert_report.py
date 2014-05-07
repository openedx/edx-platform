from django.core.management.base import BaseCommand
from certificates.models import GeneratedCertificate
from django.contrib.auth.models import User
from optparse import make_option
from django.conf import settings
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from django.db.models import Count


class Command(BaseCommand):

    help = """

    Generate a certificate status report for all courses that have ended.
    This command does not do anything other than report the current
    certificate status.

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

    def _ended_courses(self):
        for course_id in [course  # all courses in COURSE_LISTINGS
                for sub in settings.COURSE_LISTINGS
                    for course in settings.COURSE_LISTINGS[sub]]:
            course = modulestore().get_course(course_id)
            if course.has_ended():
                yield course_id

    def handle(self, *args, **options):

        # Find all courses that have ended

        if options['course']:
            ended_courses = [options['course']]
        else:
            ended_courses = self._ended_courses()

        cert_data = {}

        for course_id in ended_courses:

            # find students who are enrolled
            print "Looking up certificate states for {0}".format(course_id)
            enrolled_students = User.objects.filter(
                    courseenrollment__course_id=course_id,
                    courseenrollment__is_active=True)
            cert_data[course_id] = {'enrolled': enrolled_students.count()}

            tallies = GeneratedCertificate.objects.filter(
                        course_id__exact=course_id).values('status').annotate(
                            dcount=Count('status'))
            cert_data[course_id].update(
                    {status['status']: status['dcount']
                                        for status in tallies})

        # all states we have seen far all courses
        status_headings = set(
                [status for course in cert_data
                    for status in cert_data[course]])

        # print the heading for the report
        print "{:>20}".format("course ID"),
        print ' '.join(["{:>12}".format(heading)
                            for heading in status_headings])

        # print the report
        for course_id in cert_data:
            print "{0:>20}".format(course_id[0:18]),
            for heading in status_headings:
                if heading in cert_data[course_id]:
                    print "{:>12}".format(cert_data[course_id][heading]),
                else:
                    print " " * 12,
            print
