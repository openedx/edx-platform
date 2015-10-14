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


def get_user_from_identifier(identifier):
    """
     This function takes the string identifier and fetch relevant user object from database
    """
    identifier = identifier.strip()
    if '@' in identifier:
        user = User.objects.get(email=identifier)
    else:
        user = User.objects.get(username=identifier)
    return user


class Command(BaseCommand):
    """
    Management command to set or get the certificate whitelist
    for a given user(s)/course
    """

    help = """
    Sets or gets the certificate whitelist for a given
    user(s)/course

        Add a user or list of users to the whitelist for a course

        $ ... cert_whitelist --add joe -c "MITx/6.002x/2012_Fall"
        OR
        $ ... cert_whitelist --add joe,jenny,tom,jerry -c "MITx/6.002x/2012_Fall"

        Remove a user or list of users from the whitelist for a course

        $ ... cert_whitelist --del joe -c "MITx/6.002x/2012_Fall"
        OR
        $ ... cert_whitelist --del joe,jenny,tom,jerry -c "MITx/6.002x/2012_Fall"

        Print out who is whitelisted for a course

        $ ... cert_whitelist -c "MITx/6.002x/2012_Fall"

    """

    option_list = BaseCommand.option_list + (
        make_option('-a', '--add',
                    metavar='USER',
                    dest='add',
                    default=False,
                    help='user or list of users to add to the certificate whitelist'),

        make_option('-d', '--del',
                    metavar='USER',
                    dest='del',
                    default=False,
                    help='user or list of users to remove from the certificate whitelist'),

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

        def update_user_whitelist(username, add=True):
            """
            Update the status of whitelist user(s)
            """
            user = get_user_from_identifier(username)
            cert_whitelist, _created = CertificateWhitelist.objects.get_or_create(
                user=user, course_id=course
            )
            cert_whitelist.whitelist = add
            cert_whitelist.save()

        # try to parse the serialized course key into a CourseKey
        try:
            course = CourseKey.from_string(course_id)
        except InvalidKeyError:
            print(("Course id {} could not be parsed as a CourseKey; "
                   "falling back to SSCK.from_dep_str").format(course_id))
            course = SlashSeparatedCourseKey.from_deprecated_string(course_id)

        if options['add'] and options['del']:
            raise CommandError("Either remove or add a user, not both")

        if options['add'] or options['del']:
            user_str = options['add'] or options['del']
            add_to_whitelist = True if options['add'] else False
            users_list = user_str.split(",")
            for username in users_list:
                if username.strip():
                    update_user_whitelist(username, add=add_to_whitelist)

        whitelist = CertificateWhitelist.objects.filter(course_id=course)
        wl_users = '\n'.join(
            "{u.user.username} {u.user.email} {u.whitelist}".format(u=u)
            for u in whitelist
        )
        print("User whitelist for course {0}:\n{1}".format(course_id, wl_users))
