"""
Management command which sets or gets the certificate whitelist for a given
user/course
"""


from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

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

    def add_arguments(self, parser):
        parser.add_argument(
            '-a', '--add',
            metavar='USER',
            dest='add',
            default=False,
            help='user or list of users to add to the certificate whitelist'
        )
        parser.add_argument(
            '-d', '--del',
            metavar='USER',
            dest='del',
            default=False,
            help='user or list of users to remove from the certificate whitelist'
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
        course = CourseKey.from_string(course_id)

        if options['add'] and options['del']:
            raise CommandError("Either remove or add a user, not both")

        if options['add'] or options['del']:
            user_str = options['add'] or options['del']
            add_to_whitelist = True if options['add'] else False  # pylint: disable=simplifiable-if-expression
            users_list = user_str.split(",")
            for username in users_list:
                username = username.strip()
                if username:
                    update_user_whitelist(username, add=add_to_whitelist)

        whitelist = CertificateWhitelist.objects.filter(course_id=course)
        wl_users = '\n'.join(
            "{u.user.username} {u.user.email} {u.whitelist}".format(u=u)
            for u in whitelist
        )
        print(f"User whitelist for course {course_id}:\n{wl_users}")
