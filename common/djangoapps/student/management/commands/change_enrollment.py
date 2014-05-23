from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from optparse import make_option
from student.models import CourseEnrollment, User

from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):

    help = """
    Changes the enrollment status for students that meet
    the criteria specified by the parameters to this command.

    Example:

        Change enrollment for user joe from audit to honor:

          $ ... change_enrollment -u joe -c some/course/id --from audit --to honor

        Change enrollment for all users in some/course/id from audit to honor

          $ ... change_enrollment -c some/course/id --from audit --to honor

    """

    option_list = BaseCommand.option_list + (
        make_option('-f', '--from',
                    metavar='FROM_MODE',
                    dest='from_mode',
                    default=False,
                    help='move from this enrollment mode'),
        make_option('-t', '--to',
                    metavar='TO_MODE',
                    dest='to_mode',
                    default=False,
                    help='move to this enrollment mode'),
        make_option('-u', '--user',
                    metavar='USER',
                    dest='user',
                    default=False,
                    help="User to move, if not specified will move all users in the course"),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course_id',
                    default=False,
                    help="course id to use for transfer"),
        make_option('-n', '--noop',
                    action='store_true',
                    dest='noop',
                    default=False,
                    help="display what will be done but don't actually do anything")

    )

    def handle(self, *args, **options):
        if not options['course_id']:
            raise CommandError("You must specify a course id for this command")
        if not options['from_mode'] or not options['to_mode']:
            raise CommandError('You must specify a "to" and "from" mode as parameters')

        try:
            course_key = CourseKey.from_string(options['course_id'])
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(options['course_id'])

        filter_args = dict(
            course_id=course_key,
            mode=options['from_mode']
        )
        if options['user']:
            if '@' in options['user']:
                user = User.objects.get(email=options['user'])
            else:
                user = User.objects.get(username=options['user'])
            filter_args['user'] = user
        enrollments = CourseEnrollment.objects.filter(**filter_args)
        if options['noop']:
            print "Would have changed {num_enrollments} students from {from_mode} to {to_mode}".format(
                num_enrollments=enrollments.count(),
                from_mode=options['from_mode'],
                to_mode=options['to_mode']
            )
        else:
            for enrollment in enrollments:
                enrollment.update_enrollment(mode=options['to_mode'])
                enrollment.save()
