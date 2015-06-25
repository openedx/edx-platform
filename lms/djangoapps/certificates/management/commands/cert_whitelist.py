"""
Management command which sets or gets the certificate whitelist for a given
user/course
"""
from __future__ import print_function
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from certificates.models import CertificateWhitelist
from django.contrib.auth.models import User


class Command(BaseCommand):

    help = """
    Sets or gets the certificate whitelist for a given
    user/course

        Add a user to the whitelist for a course

        $ ... cert_whitelist --add joe -c "MITx/6.002x/2012_Fall"

        Remove a user from the whitelist for a course

        $ ... cert_whitelist --del joe -c "MITx/6.002x/2012_Fall"

        Print out who is whitelisted for a course

        $ ... cert_whitelist -c "MITx/6.002x/2012_Fall"

    """

    option_list = BaseCommand.option_list + (
        make_option('-a', '--add',
                    metavar='USER',
                    dest='add',
                    default=False,
                    help='user to add to the certificate whitelist'),

        make_option('-d', '--del',
                    metavar='USER',
                    dest='del',
                    default=False,
                    help='user to remove from the certificate whitelist'),

        make_option('-c', '--course-id',
                    metavar='COURSE_ID',
                    dest='course_id',
                    default=False,
                    help="course id to query"),
    )

    def handle(self, *args, **options):
        course_id = options['course_id']
        if not course_id:
            raise CommandError("You must specify a course-id")

        # try to parse the serialized course key into a CourseKey
        try:
            course = CourseKey.from_string(course_id)
        except InvalidKeyError:
            print("Course id {} could not be parsed as a CourseKey; falling back to SSCK.from_dep_str".format(course_id))
            course = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        if options['add'] and options['del']:
            raise CommandError("Either remove or add a user, not both")

        if options['add'] or options['del']:
            user_str = options['add'] or options['del']
            if '@' in user_str:
                user = User.objects.get(email=user_str)
            else:
                user = User.objects.get(username=user_str)

            cert_whitelist, _created = \
                CertificateWhitelist.objects.get_or_create(
                    user=user, course_id=course)
            if options['add']:
                cert_whitelist.whitelist = True
            elif options['del']:
                cert_whitelist.whitelist = False
            cert_whitelist.save()

        whitelist = CertificateWhitelist.objects.filter(course_id=course)
        wl_users = '\n'.join(
            "{u.user.username} {u.user.email} {u.whitelist}".format(u=u)
            for u in whitelist
        )
        print("User whitelist for course {0}:\n{1}".format(course_id, wl_users))
