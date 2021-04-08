"""
Management command which sets or gets the certificate allowlist for a given
user/course
"""


from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.api import (
    can_be_added_to_allowlist,
    create_or_update_certificate_allowlist_entry, remove_allowlist_entry,
)
from lms.djangoapps.certificates.models import CertificateWhitelist


User = get_user_model()


def get_user_from_identifier(identifier):
    """
    This function takes the string identifier and fetch relevant user object from database
    """
    user = User.objects.filter(Q(username=identifier) | Q(email=identifier)).first()
    if not user:
        raise CommandError("User {} does not exist.".format(identifier))
    return user


def update_allowlist(user, course, enable):
    """
    Update the status of a user on the allowlist.
    """
    if enable and can_be_added_to_allowlist(user, course):
        create_or_update_certificate_allowlist_entry(
            user,
            course,
            "Updated by mngmt cmd",
            enable
        )
    elif not enable:
        remove_allowlist_entry(user, course)
    else:
        print(f"Failed to process allowlist request for student {user.id} in course {course} and enable={enable}.")


class Command(BaseCommand):
    """
    Management command to set or get the certificate allowlist
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

    def add_arguments(self, parser):
        parser.add_argument(
            '-a', '--add',
            metavar='USER',
            dest='add',
            default=False,
            help='user or list of users to add to the certificate allowlist'
        )
        parser.add_argument(
            '-d', '--del',
            metavar='USER',
            dest='del',
            default=False,
            help='user or list of users to remove from the certificate allowlist'
        )
        parser.add_argument(
            '-c', '--course-id',
            metavar='COURSE_ID',
            dest='course_id',
            default=False,
            help="course id to query"
        )

    def handle(self, *args, **options):
        course_id = options['course_id']
        if not course_id:
            raise CommandError("You must specify a course-id")

        # try to parse the serialized course key into a CourseKey
        course = CourseKey.from_string(course_id)

        if options['add'] and options['del']:
            raise CommandError("Either remove or add a user, not both")

        if options['add'] or options['del']:
            user_str = options['add'] or options['del']
            enable = True if options['add'] else False  # pylint: disable=simplifiable-if-expression

            users_list = user_str.split(",")
            for username in users_list:
                username = username.strip()
                if username:
                    try:
                        user = get_user_from_identifier(username)
                    except CommandError as error:
                        print(f"Error occurred retrieving user {username}: {error}")
                    else:
                        update_allowlist(user, course, enable)

        whitelist = CertificateWhitelist.objects.filter(course_id=course)
        wl_users = '\n'.join(
            "{u.user.username} {u.user.email} {u.whitelist}".format(u=u)
            for u in whitelist
        )
        print(f"Allowlist for course {course_id}:\n{wl_users}")
