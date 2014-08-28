"""
Deactivate bulk_email by email address or username.
"""
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from bulk_email.models import Optout
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator
from student.models import CourseEnrollment, get_user_by_username_or_email
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Django management command to deactivate bulk_email by email address or username
    """
    help = '''Deactivate bulk_email by email address or username'''
    args = '<email or username>'
    option_list = BaseCommand.option_list + (
        make_option('-c', '--course_id',
                    action="store",
                    dest='course_id',
                    default=None,
                    help="Change specific course state"),
        make_option('-r', '--reactivate',
                    action="store_true",
                    dest='reactivate',
                    default=False,
                    help='Reactivates bulk_email (change force_diabled to False)')
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('Must called with arguments: {}'.format(self.args))
        try:
            user = get_user_by_username_or_email(args[0])
        except:
            raise CommandError('No user exists [ {} ]'.format(args[0]))

        course_id = options['course_id']
        reactivate = options['reactivate']
        if course_id:
            try:
                course_id = CourseLocator.from_string(course_id)
            except InvalidKeyError:
                raise CommandError("'{}' is an invalid course_id".format(course_id))
            if not modulestore().get_course(course_id):
                raise CommandError("The specified course does not exist.")
            self.change_optout_state(user, course_id, reactivate)
        else:
            course_enrollments = CourseEnrollment.enrollments_for_user(user)
            for enrollment in course_enrollments:
                course_id = enrollment.course_id
                self.change_optout_state(user, course_id, reactivate)

    def change_optout_state(self, user, course_id, reactivate):
        optout_object = Optout.objects.filter(user=user, course_id=course_id)
        if reactivate:
            optout_object.delete()
            print ('Activating: {}').format(course_id)
        else:
            if not optout_object:
                Optout.objects.create(user=user, course_id=course_id, force_disabled=True)
                print ('Force Deactivating: {}').format(course_id)
            else:
                update_optout = Optout.objects.filter(user=user, course_id=course_id, force_disabled=False).update(force_disabled=True)
                if update_optout:
                    print ('Updated force_disabled flag: {}').format(course_id)
