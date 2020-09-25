from django.core.urlresolvers import reverse
from pyquery import PyQuery as pq

from course_action_state.models import CourseRerunState
from openedx.core.djangolib.testing.philu_utils import configure_philu_theme
from student.models import CourseEnrollment
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from ..models import CourseCard, CourseOverview
from .helpers import disable_course_card, initialize_test_user, set_course_dates


class CourseCardBaseClass(ModuleStoreTestCase):

    password = 'test'
    # Always keep NUMBER_OF_COURSES greater than equal to 2
    NUMBER_OF_COURSES = 4

    def setUp(self):
        super(CourseCardBaseClass, self).setUp()

        self.user = initialize_test_user(password=self.password)
        self.staff = initialize_test_user(is_staff=True, password=self.password)

        org = 'edX'
        course_number_f = 'CS10{}'
        course_run_f = '2015_Q{}'
        display_name_f = 'test course {}'

        self.courses = [
            CourseFactory.create(org=org, number=course_number_f.format(str(i)), run=course_run_f.format(str(i)),
                                 display_name=display_name_f.format(str(i)), default_store=ModuleStoreEnum.Type.split)
            for i in range(1, self.NUMBER_OF_COURSES + 1)
        ]

        for course in self.courses:
            course.save()
            CourseOverview._create_or_update(course=course).save()
            CourseCard(course_id=course.id, course_name=course.display_name, is_enabled=True).save()

    @classmethod
    def setUpClass(cls):
        super(CourseCardBaseClass, cls).setUpClass()
        configure_philu_theme()


class CourseCardViewBaseClass(CourseCardBaseClass):

    def test_enabled_courses_view(self):
        course = self.courses[0]
        disable_course_card(course)

        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(reverse('courses'))

        # desired output is NUMBER_OF_COURSES since despite one course's course card being disabled,
        # Staff user is still able to see it in the course list
        self.assertEqual(pq(response.content)("article.course").length, len(self.courses))

        self.client.logout()

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(reverse('courses'))

        # desired output is (NUMBER_OF_COURSES - 1) since one course's course card has been disabled,
        # and normal user should not be able to see disabled courses
        self.assertEqual(pq(response.content)("article.course").length, len(self.courses)-1)

    def test_no_scheduled_or_ended_classes_case(self):
        ended_course = self.courses[0]
        scheduled_courses = self.courses[2:]

        set_course_dates(ended_course, -90, -76, -75, -60)

        for scheduled_course in scheduled_courses:
            set_course_dates(scheduled_course, 30, 59, 60, 75)

        response = self.client.get(reverse('courses'))

        # Desired output is 2 since there is one course that has not been assigned
        # any start or end date and another course that has already ended
        self.assertEqual(pq(response.content)("span.no-scheduled-class").length, 2)

    def test_ongoing_course_start_date(self):
        ongoing_course = self.courses[0]
        set_course_dates(ongoing_course, -15, 5, 16, 30)

        response = self.client.get(reverse('courses'))

        # Desired Result is one since only one ongoing course
        self.assertEqual(pq(response.content)('span.text:contains("Start Date")').length, 1)

    def test_invitaion_only_course(self):
        org = 'edX'
        course_number = 'CS10' + str(self.NUMBER_OF_COURSES + 1)
        course_run = '2015_Q1'
        display_name = 'test course ' + str(self.NUMBER_OF_COURSES + 1)

        course = CourseFactory.create(
            org=org,
            number=course_number,
            run=course_run,
            display_name=display_name,
            default_store=ModuleStoreEnum.Type.split,
            metadata={"invitation_only": True}
        )

        course.save()
        CourseOverview._create_or_update(course=course).save()
        CourseCard(course_id=course.id, course_name=course.display_name, is_enabled=True).save()

        self.client.login(username=self.staff.username, password=self.password)
        response = self.client.get(reverse('courses'))

        # desired output is NUMBER_OF_COURSES since despite the newly added course, the course being
        # invitation only means only users enrolled in it can see them and not even staff members (which aren't
        # enrolled can view
        self.assertEqual(pq(response.content)("article.course").length, self.NUMBER_OF_COURSES)

        self.client.logout()

        self.client.login(username=self.user.username, password=self.password)
        response = self.client.get(reverse('courses'))

        # desired output is NUMBER_OF_COURSES since one course's course card is invitation only,
        # and normal user will not be able to see invitation only courses unless enrolled
        self.assertEqual(pq(response.content)("article.course").length, self.NUMBER_OF_COURSES)

        CourseEnrollment.enroll(self.user, course.id)

        response = self.client.get(reverse('courses'))

        # desired output is NUMBER_OF_COURSES + 1 since user is enrolled in the invitation only course
        self.assertEqual(pq(response.content)("article.course").length, self.NUMBER_OF_COURSES + 1)

    def test_enrolled_course_date(self):
        date_time_format = '%b %-d, %Y'
        course = self.courses[0]

        self.client.login(username=self.user.username, password=self.password)

        # disable all other courses
        for c in self.courses[1:]:
            disable_course_card(c)

        course_overview = set_course_dates(course, -30, -10, -1, 30)

        response = self.client.get(reverse('courses'))

        self.assertContains(response, course_overview.start.strftime(date_time_format))

        course_overview = set_course_dates(course, -30, -5, -1, 30)

        CourseEnrollment.enroll(self.user, course.id)

        response = self.client.get(reverse('courses'))

        self.assertContains(response, course_overview.start.strftime(date_time_format))

        re_run_course = CourseFactory.create(
            org=course.org,
            number=course.number,
            run='2015_Q2',
            display_name=course.display_name + ' - re run',
            default_store=ModuleStoreEnum.Type.split
        )

        CourseRerunState.objects.initiated(course.id, re_run_course.id, self.staff,
                                           display_name=re_run_course.display_name)
        CourseRerunState.objects.succeeded(course_key=re_run_course.id)

        re_run_course.save()

        set_course_dates(course, -30, -15, -10, -1)

        re_run_course_overview = set_course_dates(re_run_course, 1, 10, 15, 30)

        response = self.client.get(reverse('courses'))

        self.assertContains(response, re_run_course_overview.start.strftime(date_time_format))
