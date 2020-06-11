from datetime import timedelta

from openedx.features.student_account.constants import NON_ACTIVE_COURSE_NOTIFICATION
from custom_settings.models import CustomSettings
from lms.djangoapps.onboarding.helpers import get_current_utc_date
from openedx.core.djangoapps.timed_notification.core import get_course_first_chapter_link
from openedx.features.student_account.helpers import get_non_active_course
from student.tests.factories import CourseEnrollmentFactory
from openedx.features.course_card.tests.helpers import initialize_test_user, set_course_dates
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class DisplayNotification(ModuleStoreTestCase):
    password = 'test'

    def setUp(self):
        super(DisplayNotification, self).setUp()

        self.user = initialize_test_user(password=self.password)
        self.staff = initialize_test_user(is_staff=True, password=self.password)


class DisplayNotificationTest(DisplayNotification):

    def test_non_active_course(self):
        courses = create_courses(self.user, 1)
        set_course_dates(courses[0], -30, -10, -3, 30)
        non_active_course = get_non_active_course(self.user)
        self.assertEqual(len(non_active_course), 0)

    def test_one_active_course(self):
        courses = create_courses(self.user, 1)
        set_course_dates(courses[0], -30, -10, -7, 30)
        error = NON_ACTIVE_COURSE_NOTIFICATION % (courses[0].display_name,
                                                  get_course_first_chapter_link(course=courses[0]))
        non_active_course = get_non_active_course(self.user)
        self.assertEqual(error, non_active_course[0]['alert'])

    def test_non_active_course_custom_settings(self):
        courses = create_courses(self.user, 1)
        set_course_dates(courses[0], -30, -10, -30, 30)
        save_course_custom_settings(courses[0].id, get_current_utc_date())
        non_active_course = get_non_active_course(self.user)
        self.assertEqual(len(non_active_course), 0)

    def test_one_active_course_custom_settings(self):
        courses = create_courses(self.user, 1)
        set_course_dates(courses[0], -30, -10, -30, 30)
        save_course_custom_settings(courses[0].id, get_current_utc_date() - timedelta(days=7))
        non_active_course = get_non_active_course(self.user)
        error = NON_ACTIVE_COURSE_NOTIFICATION % (courses[0].display_name,
                                                  get_course_first_chapter_link(course=courses[0]))
        self.assertEqual(error, non_active_course[0]['alert'])

    def test_two_courses_one_active_course(self):
        courses = create_courses(self.user, 2)
        set_course_dates(courses[0], -30, -10, -2, 30)
        set_course_dates(courses[1], -30, -10, -7, 30)
        error = NON_ACTIVE_COURSE_NOTIFICATION % (courses[1].display_name,
                                                  get_course_first_chapter_link(course=courses[1]))
        non_active_course = get_non_active_course(self.user)
        self.assertEqual(error, non_active_course[0]['alert'])


def create_courses(user, no_of_courses):
    org = 'edX'
    course_number_f = 'CS10{}'
    course_run = '2019_Q1'
    display_name_f = 'test course {}'

    courses = [
        CourseFactory.create(org=org, number=course_number_f.format(str(i)), run=course_run,
                             display_name=display_name_f.format(str(i)), default_store=ModuleStoreEnum.Type.split)
        for i in range(1, no_of_courses + 1)
    ]

    for course in courses:
        CourseEnrollmentFactory.create(user=user, course_id=course.id)
    return courses


def save_course_custom_settings(course_key_string, datetime):
    course_settings = CustomSettings(id=course_key_string, course_short_id=1, course_open_date=datetime)
    course_settings.save()
    return course_settings
