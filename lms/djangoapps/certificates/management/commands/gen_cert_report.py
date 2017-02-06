"""
Generate a report of certificate statuses
"""

from django.core.management.base import BaseCommand, CommandError
from certificates.models import GeneratedCertificate
from django.contrib.auth.models import User
from optparse import make_option
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.db.models import Count


class Command(BaseCommand):
    """
    Management command to generate a certificate status
    report for a given course.
    """

    help = """

    Generate a certificate status report for a given course.
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

    def handle(self, *args, **options):

        # Find all courses that have ended

        if options['course']:
            try:
                course_id = CourseKey.from_string(options['course'])
            except InvalidKeyError:
                print ("Course id {} could not be parsed as a CourseKey; "
                       "falling back to SSCK.from_dep_str").format(options['course'])
                course_id = SlashSeparatedCourseKey.from_deprecated_string(options['course'])
        else:
            raise CommandError("You must specify a course")

        cert_data = {}

        # find students who are active
        # number of enrolled students = downloadable + notpassing
        print "Looking up certificate states for {0}".format(options['course'])
        enrolled_current = User.objects.filter(
            courseenrollment__course_id=course_id,
            courseenrollment__is_active=True
        )
        enrolled_total = User.objects.filter(
            courseenrollment__course_id=course_id
        )
        verified_enrolled = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_id,
            mode__exact='verified'
        )
        honor_enrolled = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_id,
            mode__exact='honor'
        )
        audit_enrolled = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_id,
            mode__exact='audit'
        )

        cert_data[course_id] = {
            'enrolled_current': enrolled_current.count(),
            'enrolled_total': enrolled_total.count(),
            'verified_enrolled': verified_enrolled.count(),
            'honor_enrolled': honor_enrolled.count(),
            'audit_enrolled': audit_enrolled.count()
        }

        status_tally = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_id
        ).values('status').annotate(
            dcount=Count('status')
        )

        cert_data[course_id].update(
            {
                status['status']: status['dcount'] for status in status_tally
            }
        )

        mode_tally = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
            course_id__exact=course_id,
            status__exact='downloadable'
        ).values('mode').annotate(
            dcount=Count('mode')
        )
        cert_data[course_id].update(
            {mode['mode']: mode['dcount'] for mode in mode_tally}
        )

        # all states we have seen far all courses
        status_headings = sorted(
            set([status for course in cert_data for status in cert_data[course]])
        )

        # print the heading for the report
        print "{:>26}".format("course ID"),
        print ' '.join(["{:>16}".format(heading) for heading in status_headings])

        # print the report
        print "{0:>26}".format(course_id.to_deprecated_string()),
        for heading in status_headings:
            if heading in cert_data[course_id]:
                print "{:>16}".format(cert_data[course_id][heading]),
            else:
                print " " * 16,
        print
