""" Shared behavior between create_test_users and create_random_users """
from xmodule.modulestore.django import modulestore

from lms.djangoapps.instructor.access import allow_access
from openedx.core.djangoapps.user_authn.views.registration_form import AccountCreationForm
from common.djangoapps.student.helpers import do_create_account
from common.djangoapps.student.models import CourseEnrollment


def create_users(
    course_key,
    user_data,
    enrollment_mode=None,
    course_staff=False,
    activate=False
):
    """Create users, enrolling them in course_key if it's not None"""
    for single_user_data in user_data:
        account_creation_form = AccountCreationForm(
            data=single_user_data,
            tos_required=False
        )

        (user, _, _) = do_create_account(account_creation_form)

        if activate:
            user.is_active = True
            user.save()

        if course_key is not None:
            CourseEnrollment.enroll(user, course_key, mode=enrollment_mode)
            if course_staff:
                course = modulestore().get_course(course_key, depth=1)
                allow_access(course, user, 'staff', send_email=False)

        if course_key and course_staff:
            print('Created user {} as course staff'.format(user.username))
        else:
            print('Created user {}'.format(user.username))
