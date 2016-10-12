"""
test views
"""
import datetime
import json
import re
import pytz
import ddt
import urlparse
from dateutil.tz import tzutc
from mock import patch, MagicMock
from nose.plugins.attrib import attr

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware.courses import get_course_by_id
from courseware.tests.factories import StudentModuleFactory
from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tabs import get_course_tab_list
from courseware.testutils import FieldOverrideTestMixin
from django_comment_client.utils import has_forum_access
from django_comment_common.models import FORUM_ROLE_ADMINISTRATOR
from django_comment_common.utils import are_permissions_roles_seeded
from instructor.access import (
    allow_access,
    list_with_level,
)

from django.conf import settings
from django.core.urlresolvers import reverse, resolve
from django.utils.translation import ugettext as _
from django.utils.timezone import UTC
from django.test.utils import override_settings
from django.test import RequestFactory
from edxmako.shortcuts import render_to_response
from request_cache.middleware import RequestCache
from opaque_keys.edx.keys import CourseKey
from student.roles import (
    CourseCcxCoachRole,
    CourseInstructorRole,
    CourseStaffRole,
)
from student.models import (
    CourseEnrollment,
    CourseEnrollmentAllowed,
)
from student.tests.factories import (
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)

from xmodule.x_module import XModuleMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    ItemFactory,
    SampleCourseFactory,
)
from ccx_keys.locator import CCXLocator

from lms.djangoapps.ccx.models import CustomCourseForEdX
from lms.djangoapps.ccx.overrides import get_override_for_ccx, override_field_for_ccx
from lms.djangoapps.ccx.tests.factories import CcxFactory
from lms.djangoapps.ccx.tests.utils import (
    CcxTestCase,
    flatten,
)
from lms.djangoapps.ccx.utils import (
    ccx_course,
    is_email,
)
from lms.djangoapps.ccx.views import get_date

from xmodule.modulestore.django import modulestore


def intercept_renderer(path, context):
    """
    Intercept calls to `render_to_response` and attach the context dict to the
    response for examination in unit tests.
    """
    # I think Django already does this for you in their TestClient, except
    # we're bypassing that by using edxmako.  Probably edxmako should be
    # integrated better with Django's rendering and event system.
    response = render_to_response(path, context)
    response.mako_context = context
    response.mako_template = path
    return response


def ccx_dummy_request():
    """
    Returns dummy request object for CCX coach tab test
    """
    factory = RequestFactory()
    request = factory.get('ccx_coach_dashboard')
    request.user = MagicMock()

    return request


def setup_students_and_grades(context):
    """
    Create students and set their grades.
    :param context:  class reference
    """
    if context.course:
        context.student = student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=context.course.id)

        context.student2 = student2 = UserFactory.create()
        CourseEnrollmentFactory.create(user=student2, course_id=context.course.id)

        # create grades for self.student as if they'd submitted the ccx
        for chapter in context.course.get_children():
            for i, section in enumerate(chapter.get_children()):
                for j, problem in enumerate(section.get_children()):
                    # if not problem.visible_to_staff_only:
                    StudentModuleFactory.create(
                        grade=1 if i < j else 0,
                        max_grade=1,
                        student=context.student,
                        course_id=context.course.id,
                        module_state_key=problem.location
                    )

                    StudentModuleFactory.create(
                        grade=1 if i > j else 0,
                        max_grade=1,
                        student=context.student2,
                        course_id=context.course.id,
                        module_state_key=problem.location
                    )


def unhide(unit):
    """
    Recursively unhide a unit and all of its children in the CCX
    schedule.
    """
    unit['hidden'] = False
    for child in unit.get('children', ()):
        unhide(child)


class TestAdminAccessCoachDashboard(CcxTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        super(TestAdminAccessCoachDashboard, self).setUp()
        self.make_coach()
        ccx = self.make_ccx()
        ccx_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        self.url = reverse('ccx_coach_dashboard', kwargs={'course_id': ccx_key})

    def test_staff_access_coach_dashboard(self):
        """
        User is staff, should access coach dashboard.
        """
        staff = self.make_staff()
        self.client.login(username=staff.username, password="test")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_instructor_access_coach_dashboard(self):
        """
        User is instructor, should access coach dashboard.
        """
        instructor = self.make_instructor()
        self.client.login(username=instructor.username, password="test")

        # Now access URL
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_forbidden_user_access_coach_dashboard(self):
        """
        Assert user with no access must not see dashboard.
        """
        user = UserFactory.create(password="test")
        self.client.login(username=user.username, password="test")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


@attr(shard=1)
@override_settings(
    XBLOCK_FIELD_DATA_WRAPPERS=['lms.djangoapps.courseware.field_overrides:OverrideModulestoreFieldData.wrap'],
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS=['ccx.overrides.CustomCoursesForEdxOverrideProvider'],
)
class TestCCXProgressChanges(CcxTestCase, LoginEnrollmentTestCase):
    """
    Tests ccx schedule changes in progress page
    """
    @classmethod
    def setUpClass(cls):
        """
        Set up tests
        """
        super(TestCCXProgressChanges, cls).setUpClass()
        start = datetime.datetime(2016, 7, 1, 0, 0, tzinfo=tzutc())
        due = datetime.datetime(2016, 7, 8, 0, 0, tzinfo=tzutc())

        cls.course = course = CourseFactory.create(enable_ccx=True, start=start)
        chapter = ItemFactory.create(start=start, parent=course, category=u'chapter')
        sequential = ItemFactory.create(
            parent=chapter,
            start=start,
            due=due,
            category=u'sequential',
            metadata={'graded': True, 'format': 'Homework'}
        )
        vertical = ItemFactory.create(
            parent=sequential,
            start=start,
            due=due,
            category=u'vertical',
            metadata={'graded': True, 'format': 'Homework'}
        )

        # Trying to wrap the whole thing in a bulk operation fails because it
        # doesn't find the parents. But we can at least wrap this part...
        with cls.store.bulk_operations(course.id, emit_signals=False):
            flatten([ItemFactory.create(
                parent=vertical,
                start=start,
                due=due,
                category="problem",
                data=StringResponseXMLFactory().build_xml(answer='foo'),
                metadata={'rerandomize': 'always'}
            )] for _ in xrange(2))

    def assert_progress_summary(self, ccx_course_key, due):
        """
        assert signal and schedule update.
        """
        student = UserFactory.create(is_staff=False, password="test")
        CourseEnrollment.enroll(student, ccx_course_key)
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=student).exists()
        )

        # login as student
        self.client.login(username=student.username, password="test")
        progress_page_response = self.client.get(
            reverse('progress', kwargs={'course_id': ccx_course_key})
        )
        grade_summary = progress_page_response.mako_context['courseware_summary']  # pylint: disable=no-member
        chapter = grade_summary[0]
        section = chapter['sections'][0]
        progress_page_due_date = section.due.strftime("%Y-%m-%d %H:%M")
        self.assertEqual(progress_page_due_date, due)

    @patch('ccx.views.render_to_response', intercept_renderer)
    @patch('courseware.views.views.render_to_response', intercept_renderer)
    @patch.dict('django.conf.settings.FEATURES', {'CUSTOM_COURSES_EDX': True})
    def test_edit_schedule(self):
        """
        Get CCX schedule, modify it, save it.
        """
        self.make_coach()
        ccx = self.make_ccx()
        ccx_course_key = CCXLocator.from_course_locator(self.course.id, unicode(ccx.id))
        self.client.login(username=self.coach.username, password="test")

        url = reverse('ccx_coach_dashboard', kwargs={'course_id': ccx_course_key})
        response = self.client.get(url)

        schedule = json.loads(response.mako_context['schedule'])  # pylint: disable=no-member
        self.assertEqual(len(schedule), 1)

        unhide(schedule[0])

        # edit schedule
        date = datetime.datetime.now() - datetime.timedelta(days=5)
        start = date.strftime("%Y-%m-%d %H:%M")
        due = (date + datetime.timedelta(days=3)).strftime("%Y-%m-%d %H:%M")

        schedule[0]['start'] = start
        schedule[0]['children'][0]['start'] = start
        schedule[0]['children'][0]['due'] = due
        schedule[0]['children'][0]['children'][0]['start'] = start
        schedule[0]['children'][0]['children'][0]['due'] = due

        url = reverse('save_ccx', kwargs={'course_id': ccx_course_key})
        response = self.client.post(url, json.dumps(schedule), content_type='application/json')

        self.assertEqual(response.status_code, 200)

        schedule = json.loads(response.content)['schedule']
        self.assertEqual(schedule[0]['hidden'], False)
        self.assertEqual(schedule[0]['start'], start)
        self.assertEqual(schedule[0]['children'][0]['start'], start)
        self.assertEqual(schedule[0]['children'][0]['due'], due)
        self.assertEqual(schedule[0]['children'][0]['children'][0]['due'], due)
        self.assertEqual(schedule[0]['children'][0]['children'][0]['start'], start)

        self.assert_progress_summary(ccx_course_key, due)


@attr(shard=1)
@ddt.ddt
class TestCoachDashboard(CcxTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """

    @classmethod
    def setUpClass(cls):
        super(TestCoachDashboard, cls).setUpClass()
        cls.course_disable_ccx = CourseFactory.create(enable_ccx=False)
        cls.course_with_ccx_connect_set = CourseFactory.create(enable_ccx=True, ccx_connector="http://ccx.com")

    def setUp(self):
        """
        Set up tests
        """
        super(TestCoachDashboard, self).setUp()
        # Login with the instructor account
        self.client.login(username=self.coach.username, password="test")

        # adding staff to master course.
        staff = UserFactory()
        allow_access(self.course, staff, 'staff')
        self.assertTrue(CourseStaffRole(self.course.id).has_user(staff))

        # adding instructor to master course.
        instructor = UserFactory()
        allow_access(self.course, instructor, 'instructor')
        self.assertTrue(CourseInstructorRole(self.course.id).has_user(instructor))

    def test_not_a_coach(self):
        """
        User is not a coach, should get Forbidden response.
        """
        self.make_coach()
        ccx = self.make_ccx()

        # create session of non-coach user
        user = UserFactory.create(password="test")
        self.client.login(username=user.username, password="test")
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_no_ccx_created(self):
        """
        No CCX is created, coach should see form to add a CCX.
        """
        self.make_coach()
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': unicode(self.course.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search(
            '<form action=".+create_ccx"',
            response.content))

    def test_create_ccx_with_ccx_connector_set(self):
        """
        Assert that coach cannot create ccx when ``ccx_connector`` url is set.
        """
        role = CourseCcxCoachRole(self.course_with_ccx_connect_set.id)
        role.add_users(self.coach)

        url = reverse(
            'create_ccx',
            kwargs={'course_id': unicode(self.course_with_ccx_connect_set.id)})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        error_message = _(
            "A CCX can only be created on this course through an external service."
            " Contact a course admin to give you access."
        )
        self.assertTrue(re.search(error_message, response.content))

    def test_create_ccx(self, ccx_name='New CCX'):
        """
        Create CCX. Follow redirect to coach dashboard, confirm we see
        the coach dashboard for the new CCX.
        """

        self.make_coach()
        url = reverse(
            'create_ccx',
            kwargs={'course_id': unicode(self.course.id)})

        response = self.client.post(url, {'name': ccx_name})
        self.assertEqual(response.status_code, 302)
        url = response.get('location')  # pylint: disable=no-member
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Get the ccx_key
        path = urlparse.urlparse(url).path
        resolver = resolve(path)
        ccx_key = resolver.kwargs['course_id']

        course_key = CourseKey.from_string(ccx_key)

        self.assertTrue(CourseEnrollment.is_enrolled(self.coach, course_key))
        self.assertTrue(re.search('id="ccx-schedule"', response.content))

        # check if the max amount of student that can be enrolled has been overridden
        ccx = CustomCourseForEdX.objects.get()
        course_enrollments = get_override_for_ccx(ccx, self.course, 'max_student_enrollments_allowed')
        self.assertEqual(course_enrollments, settings.CCX_MAX_STUDENTS_ALLOWED)

        # assert ccx creator has role=staff
        role = CourseStaffRole(course_key)
        self.assertTrue(role.has_user(self.coach))

        # assert that staff and instructors of master course has staff and instructor roles on ccx
        list_staff_master_course = list_with_level(self.course, 'staff')
        list_instructor_master_course = list_with_level(self.course, 'instructor')

        # assert that forum roles are seeded
        self.assertTrue(are_permissions_roles_seeded(course_key))
        self.assertTrue(has_forum_access(self.coach.username, course_key, FORUM_ROLE_ADMINISTRATOR))

        with ccx_course(course_key) as course_ccx:
            list_staff_ccx_course = list_with_level(course_ccx, 'staff')
            # The "Coach" in the parent course becomes "Staff" on the CCX, so the CCX should have 1 "Staff"
            # user more than the parent course
            self.assertEqual(len(list_staff_master_course) + 1, len(list_staff_ccx_course))
            self.assertIn(list_staff_master_course[0].email, [ccx_staff.email for ccx_staff in list_staff_ccx_course])
            # Make sure the "Coach" on the parent course is "Staff" on the CCX
            self.assertIn(self.coach, list_staff_ccx_course)

            list_instructor_ccx_course = list_with_level(course_ccx, 'instructor')
            self.assertEqual(len(list_instructor_ccx_course), len(list_instructor_master_course))
            self.assertEqual(list_instructor_ccx_course[0].email, list_instructor_master_course[0].email)

    @ddt.data("CCX demo 1", "CCX demo 2", "CCX demo 3")
    def test_create_multiple_ccx(self, ccx_name):
        self.test_create_ccx(ccx_name)

    def test_dashboard_access_of_disabled_ccx(self):
        """
        User should not see coach dashboard if ccx is disbale in studio.
        """
        ccx = CcxFactory(course_id=self.course_disable_ccx.id, coach=self.coach)
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course_disable_ccx.id, ccx.id)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_dashboard_access_with_invalid_ccx_id(self):
        """
        User should not see coach dashboard if ccx id is invalid.
        """
        self.make_ccx()
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course_disable_ccx.id, 700)})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_date(self):
        """
        Assert that get_date returns valid date.
        """
        ccx = self.make_ccx()
        for section in self.course.get_children():
            self.assertEqual(get_date(ccx, section, 'start'), self.mooc_start)
            self.assertEqual(get_date(ccx, section, 'due'), None)
            for subsection in section.get_children():
                self.assertEqual(get_date(ccx, subsection, 'start'), self.mooc_start)
                self.assertEqual(get_date(ccx, subsection, 'due'), self.mooc_due)
                for unit in subsection.get_children():
                    self.assertEqual(get_date(ccx, unit, 'start', parent_node=subsection), self.mooc_start)
                    self.assertEqual(get_date(ccx, unit, 'due', parent_node=subsection), self.mooc_due)

    @patch('ccx.views.render_to_response', intercept_renderer)
    @patch('ccx.views.TODAY')
    def test_edit_schedule(self, today):
        """
        Get CCX schedule, modify it, save it.
        """
        today.return_value = datetime.datetime(2014, 11, 25, tzinfo=pytz.UTC)
        self.make_coach()
        ccx = self.make_ccx()
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)})
        response = self.client.get(url)
        schedule = json.loads(response.mako_context['schedule'])  # pylint: disable=no-member

        self.assertEqual(len(schedule), 2)
        self.assertEqual(schedule[0]['hidden'], False)
        # If a coach does not override dates, then dates will be imported from master course.
        self.assertEqual(
            schedule[0]['start'],
            self.chapters[0].start.strftime('%Y-%m-%d %H:%M')
        )
        self.assertEqual(
            schedule[0]['children'][0]['start'],
            self.sequentials[0].start.strftime('%Y-%m-%d %H:%M')
        )

        if self.sequentials[0].due:
            expected_due = self.sequentials[0].due.strftime('%Y-%m-%d %H:%M')
        else:
            expected_due = None
        self.assertEqual(schedule[0]['children'][0]['due'], expected_due)

        url = reverse(
            'save_ccx',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)})

        unhide(schedule[0])
        schedule[0]['start'] = u'2014-11-20 00:00'
        schedule[0]['children'][0]['due'] = u'2014-12-25 00:00'  # what a jerk!
        schedule[0]['children'][0]['children'][0]['start'] = u'2014-12-20 00:00'
        schedule[0]['children'][0]['children'][0]['due'] = u'2014-12-25 00:00'

        response = self.client.post(
            url, json.dumps(schedule), content_type='application/json'
        )

        schedule = json.loads(response.content)['schedule']
        self.assertEqual(schedule[0]['hidden'], False)
        self.assertEqual(schedule[0]['start'], u'2014-11-20 00:00')
        self.assertEqual(
            schedule[0]['children'][0]['due'], u'2014-12-25 00:00'
        )

        self.assertEqual(
            schedule[0]['children'][0]['children'][0]['due'], u'2014-12-25 00:00'
        )
        self.assertEqual(
            schedule[0]['children'][0]['children'][0]['start'], u'2014-12-20 00:00'
        )

        # Make sure start date set on course, follows start date of earliest
        # scheduled chapter
        ccx = CustomCourseForEdX.objects.get()
        course_start = get_override_for_ccx(ccx, self.course, 'start')
        self.assertEqual(str(course_start)[:-9], self.chapters[0].start.strftime('%Y-%m-%d %H:%M'))

        # Make sure grading policy adjusted
        policy = get_override_for_ccx(ccx, self.course, 'grading_policy',
                                      self.course.grading_policy)
        self.assertEqual(policy['GRADER'][0]['type'], 'Homework')
        self.assertEqual(policy['GRADER'][0]['min_count'], 8)
        self.assertEqual(policy['GRADER'][1]['type'], 'Lab')
        self.assertEqual(policy['GRADER'][1]['min_count'], 0)
        self.assertEqual(policy['GRADER'][2]['type'], 'Midterm Exam')
        self.assertEqual(policy['GRADER'][2]['min_count'], 0)
        self.assertEqual(policy['GRADER'][3]['type'], 'Final Exam')
        self.assertEqual(policy['GRADER'][3]['min_count'], 0)

    @patch('ccx.views.render_to_response', intercept_renderer)
    def test_save_without_min_count(self):
        """
        POST grading policy without min_count field.
        """
        self.make_coach()
        ccx = self.make_ccx()

        course_id = CCXLocator.from_course_locator(self.course.id, ccx.id)
        save_policy_url = reverse(
            'ccx_set_grading_policy', kwargs={'course_id': course_id})

        # This policy doesn't include a min_count field
        policy = {
            "GRADE_CUTOFFS": {
                "Pass": 0.5
            },
            "GRADER": [
                {
                    "weight": 0.15,
                    "type": "Homework",
                    "drop_count": 2,
                    "short_label": "HW"
                }
            ]
        }

        response = self.client.post(
            save_policy_url, {"policy": json.dumps(policy)}
        )
        self.assertEqual(response.status_code, 302)

        ccx = CustomCourseForEdX.objects.get()

        # Make sure grading policy adjusted
        policy = get_override_for_ccx(
            ccx, self.course, 'grading_policy', self.course.grading_policy
        )
        self.assertEqual(len(policy['GRADER']), 1)
        self.assertEqual(policy['GRADER'][0]['type'], 'Homework')
        self.assertNotIn('min_count', policy['GRADER'][0])

        save_ccx_url = reverse('save_ccx', kwargs={'course_id': course_id})
        coach_dashboard_url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': course_id}
        )
        response = self.client.get(coach_dashboard_url)
        schedule = json.loads(response.mako_context['schedule'])  # pylint: disable=no-member
        response = self.client.post(
            save_ccx_url, json.dumps(schedule), content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    @ddt.data(
        ('ccx_invite', True, 1, 'student-ids', ('enrollment-button', 'Enroll')),
        ('ccx_invite', False, 0, 'student-ids', ('enrollment-button', 'Enroll')),
        ('ccx_manage_student', True, 1, 'student-id', ('student-action', 'add')),
        ('ccx_manage_student', False, 0, 'student-id', ('student-action', 'add')),
    )
    @ddt.unpack
    def test_enroll_member_student(self, view_name, send_email, outbox_count, student_form_input_name, button_tuple):
        """
        Tests the enrollment of  a list of students who are members
        of the class.

        It tests 2 different views that use slightly different parameters,
        but that perform the same task.
        """
        self.make_coach()
        ccx = self.make_ccx()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            view_name,
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
        )
        data = {
            button_tuple[0]: button_tuple[1],
            student_form_input_name: u','.join([student.email, ]),  # pylint: disable=no-member
        }
        if send_email:
            data['email-students'] = 'Notify-students-by-email'
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(outbox), outbox_count)
        if send_email:
            self.assertIn(student.email, outbox[0].recipients())  # pylint: disable=no-member
        # a CcxMembership exists for this student
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=self.course.id, user=student).exists()
        )

    def test_ccx_invite_enroll_up_to_limit(self):
        """
        Enrolls a list of students up to the enrollment limit.

        This test is specific to one of the enrollment views: the reason is because
        the view used in this test can perform bulk enrollments.
        """
        self.make_coach()
        # create ccx and limit the maximum amount of students that can be enrolled to 2
        ccx = self.make_ccx(max_students_allowed=2)
        ccx_course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        staff = self.make_staff()
        instructor = self.make_instructor()

        # create some users
        students = [instructor, staff, self.coach] + [
            UserFactory.create(is_staff=False) for _ in range(3)
        ]

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': ccx_course_key}
        )
        data = {
            'enrollment-button': 'Enroll',
            'student-ids': u','.join([student.email for student in students]),
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # even if course is coach can enroll staff and admins of master course into ccx
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=instructor).exists()
        )
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=staff).exists()
        )
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=self.coach).exists()
        )

        # a CcxMembership exists for the first five students but not the sixth
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[3]).exists()
        )
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[4]).exists()
        )
        self.assertFalse(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[5]).exists()
        )

    def test_manage_student_enrollment_limit(self):
        """
        Enroll students up to the enrollment limit.

        This test is specific to one of the enrollment views: the reason is because
        the view used in this test cannot perform bulk enrollments.
        """
        students_limit = 1
        self.make_coach()
        staff = self.make_staff()
        ccx = self.make_ccx(max_students_allowed=students_limit)
        ccx_course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        students = [
            UserFactory.create(is_staff=False) for _ in range(2)
        ]

        url = reverse(
            'ccx_manage_student',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
        )
        # enroll the first student
        data = {
            'student-action': 'add',
            'student-id': students[0].email,
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # a CcxMembership exists for this student
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[0]).exists()
        )

        # try to enroll the second student without success
        # enroll the first student
        data = {
            'student-action': 'add',
            'student-id': students[1].email,
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # a CcxMembership does not exist for this student
        self.assertFalse(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=students[1]).exists()
        )
        error_message = 'The course is full: the limit is {students_limit}'.format(
            students_limit=students_limit
        )
        self.assertContains(response, error_message, status_code=200)

        # try to enroll the 3rd student which is staff
        data = {
            'student-action': 'add',
            'student-id': staff.email,
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # staff gets enroll
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=ccx_course_key, user=staff).exists()
        )

        self.assertEqual(CourseEnrollment.objects.num_enrolled_in_exclude_admins(ccx_course_key), 1)

        # asert that number of enroll is still 0 because staff and instructor do not count.
        CourseEnrollment.enroll(staff, self.course.id)
        self.assertEqual(CourseEnrollment.objects.num_enrolled_in_exclude_admins(self.course.id), 0)
        # assert that handles  wrong ccx id code
        ccx_course_key_fake = CCXLocator.from_course_locator(self.course.id, 55)
        self.assertEqual(CourseEnrollment.objects.num_enrolled_in_exclude_admins(ccx_course_key_fake), 0)

    @ddt.data(
        ('ccx_invite', True, 1, 'student-ids', ('enrollment-button', 'Unenroll')),
        ('ccx_invite', False, 0, 'student-ids', ('enrollment-button', 'Unenroll')),
        ('ccx_manage_student', True, 1, 'student-id', ('student-action', 'revoke')),
        ('ccx_manage_student', False, 0, 'student-id', ('student-action', 'revoke')),
    )
    @ddt.unpack
    def test_unenroll_member_student(self, view_name, send_email, outbox_count, student_form_input_name, button_tuple):
        """
        Tests the unenrollment of a list of students who are members of the class.

        It tests 2 different views that use slightly different parameters,
        but that perform the same task.
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        enrollment = CourseEnrollmentFactory(course_id=course_key)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            view_name,
            kwargs={'course_id': course_key}
        )
        data = {
            button_tuple[0]: button_tuple[1],
            student_form_input_name: u','.join([student.email, ]),  # pylint: disable=no-member
        }
        if send_email:
            data['email-students'] = 'Notify-students-by-email'
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(outbox), outbox_count)
        if send_email:
            self.assertIn(student.email, outbox[0].recipients())  # pylint: disable=no-member
        # a CcxMembership does not exists for this student
        self.assertFalse(
            CourseEnrollment.objects.filter(course_id=self.course.id, user=student).exists()
        )

    @ddt.data(
        ('ccx_invite', True, 1, 'student-ids', ('enrollment-button', 'Enroll'), 'nobody@nowhere.com'),
        ('ccx_invite', False, 0, 'student-ids', ('enrollment-button', 'Enroll'), 'nobody@nowhere.com'),
        ('ccx_invite', True, 0, 'student-ids', ('enrollment-button', 'Enroll'), 'nobody'),
        ('ccx_invite', False, 0, 'student-ids', ('enrollment-button', 'Enroll'), 'nobody'),
        ('ccx_manage_student', True, 0, 'student-id', ('student-action', 'add'), 'dummy_student_id'),
        ('ccx_manage_student', False, 0, 'student-id', ('student-action', 'add'), 'dummy_student_id'),
        ('ccx_manage_student', True, 1, 'student-id', ('student-action', 'add'), 'xyz@gmail.com'),
        ('ccx_manage_student', False, 0, 'student-id', ('student-action', 'add'), 'xyz@gmail.com'),
    )
    @ddt.unpack
    def test_enroll_non_user_student(
            self, view_name, send_email, outbox_count, student_form_input_name, button_tuple, identifier):
        """
        Tests the enrollment of a list of students who are not users yet.

        It tests 2 different views that use slightly different parameters,
        but that perform the same task.
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            view_name,
            kwargs={'course_id': course_key}
        )
        data = {
            button_tuple[0]: button_tuple[1],
            student_form_input_name: u','.join([identifier, ]),
        }
        if send_email:
            data['email-students'] = 'Notify-students-by-email'
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(outbox), outbox_count)

        # some error messages are returned for one of the views only
        if view_name == 'ccx_manage_student' and not is_email(identifier):
            self.assertContains(response, 'Could not find a user with name or email ', status_code=200)

        if is_email(identifier):
            if send_email:
                self.assertIn(identifier, outbox[0].recipients())
            self.assertTrue(
                CourseEnrollmentAllowed.objects.filter(course_id=course_key, email=identifier).exists()
            )
        else:
            self.assertFalse(
                CourseEnrollmentAllowed.objects.filter(course_id=course_key, email=identifier).exists()
            )

    @ddt.data(
        ('ccx_invite', True, 0, 'student-ids', ('enrollment-button', 'Unenroll'), 'nobody@nowhere.com'),
        ('ccx_invite', False, 0, 'student-ids', ('enrollment-button', 'Unenroll'), 'nobody@nowhere.com'),
        ('ccx_invite', True, 0, 'student-ids', ('enrollment-button', 'Unenroll'), 'nobody'),
        ('ccx_invite', False, 0, 'student-ids', ('enrollment-button', 'Unenroll'), 'nobody'),
    )
    @ddt.unpack
    def test_unenroll_non_user_student(
            self, view_name, send_email, outbox_count, student_form_input_name, button_tuple, identifier):
        """
        Unenroll a list of students who are not users yet
        """
        self.make_coach()
        course = CourseFactory.create()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(course.id, ccx.id)
        outbox = self.get_outbox()
        CourseEnrollmentAllowed(course_id=course_key, email=identifier)
        self.assertEqual(outbox, [])

        url = reverse(
            view_name,
            kwargs={'course_id': course_key}
        )
        data = {
            button_tuple[0]: button_tuple[1],
            student_form_input_name: u','.join([identifier, ]),
        }
        if send_email:
            data['email-students'] = 'Notify-students-by-email'
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(outbox), outbox_count)
        self.assertFalse(
            CourseEnrollmentAllowed.objects.filter(
                course_id=course_key, email=identifier
            ).exists()
        )


@attr(shard=1)
class TestCoachDashboardSchedule(CcxTestCase, LoginEnrollmentTestCase, ModuleStoreTestCase):
    """
    Tests of the CCX Coach Dashboard which need to modify the course content.
    """

    ENABLED_CACHES = ['default', 'mongo_inheritance_cache', 'loc_cache']

    def setUp(self):
        super(TestCoachDashboardSchedule, self).setUp()
        self.course = course = CourseFactory.create(enable_ccx=True)

        # Create a course outline
        self.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC
        )
        self.mooc_due = due = datetime.datetime(
            2010, 7, 7, 0, 0, tzinfo=pytz.UTC
        )

        self.chapters = [
            ItemFactory.create(start=start, parent=course) for _ in xrange(2)
        ]
        self.sequentials = flatten([
            [
                ItemFactory.create(parent=chapter) for _ in xrange(2)
            ] for chapter in self.chapters
        ])
        self.verticals = flatten([
            [
                ItemFactory.create(
                    start=start, due=due, parent=sequential, graded=True, format='Homework', category=u'vertical'
                ) for _ in xrange(2)
            ] for sequential in self.sequentials
        ])

        # Trying to wrap the whole thing in a bulk operation fails because it
        # doesn't find the parents. But we can at least wrap this part...
        with self.store.bulk_operations(course.id, emit_signals=False):
            blocks = flatten([  # pylint: disable=unused-variable
                [
                    ItemFactory.create(parent=vertical) for _ in xrange(2)
                ] for vertical in self.verticals
            ])

        # Create instructor account
        self.coach = UserFactory.create()
        # create an instance of modulestore
        self.mstore = modulestore()

        # Login with the instructor account
        self.client.login(username=self.coach.username, password="test")

        # adding staff to master course.
        staff = UserFactory()
        allow_access(self.course, staff, 'staff')
        self.assertTrue(CourseStaffRole(self.course.id).has_user(staff))

        # adding instructor to master course.
        instructor = UserFactory()
        allow_access(self.course, instructor, 'instructor')
        self.assertTrue(CourseInstructorRole(self.course.id).has_user(instructor))

        self.assertTrue(modulestore().has_course(self.course.id))

    def assert_elements_in_schedule(self, url, n_chapters=2, n_sequentials=4, n_verticals=8):
        """
        Helper function to count visible elements in the schedule
        """
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # the schedule contains chapters
        chapters = json.loads(response.mako_context['schedule'])  # pylint: disable=no-member
        sequentials = flatten([chapter.get('children', []) for chapter in chapters])
        verticals = flatten([sequential.get('children', []) for sequential in sequentials])
        # check that the numbers of nodes at different level are the expected ones
        self.assertEqual(n_chapters, len(chapters))
        self.assertEqual(n_sequentials, len(sequentials))
        self.assertEqual(n_verticals, len(verticals))
        # extract the locations of all the nodes
        all_elements = chapters + sequentials + verticals
        return [elem['location'] for elem in all_elements if 'location' in elem]

    def hide_node(self, node):
        """
        Helper function to set the node `visible_to_staff_only` property
        to True and save the change
        """
        node.visible_to_staff_only = True
        self.mstore.update_item(node, self.coach.id)

    @patch('ccx.views.render_to_response', intercept_renderer)
    @patch('ccx.views.TODAY')
    def test_get_ccx_schedule(self, today):
        """
        Gets CCX schedule and checks number of blocks in it.
        Hides nodes at a different depth and checks that these nodes
        are not in the schedule.
        """
        today.return_value = datetime.datetime(2014, 11, 25, tzinfo=pytz.UTC)
        self.make_coach()
        ccx = self.make_ccx()
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={
                'course_id': CCXLocator.from_course_locator(
                    self.course.id, ccx.id)
            }
        )
        # all the elements are visible
        self.assert_elements_in_schedule(url)
        # hide a vertical
        vertical = self.verticals[0]
        self.hide_node(vertical)
        locations = self.assert_elements_in_schedule(url, n_verticals=7)
        self.assertNotIn(unicode(vertical.location), locations)
        # hide a sequential
        sequential = self.sequentials[0]
        self.hide_node(sequential)
        locations = self.assert_elements_in_schedule(url, n_sequentials=3, n_verticals=6)
        self.assertNotIn(unicode(sequential.location), locations)
        # hide a chapter
        chapter = self.chapters[0]
        self.hide_node(chapter)
        locations = self.assert_elements_in_schedule(url, n_chapters=1, n_sequentials=2, n_verticals=4)
        self.assertNotIn(unicode(chapter.location), locations)


GET_CHILDREN = XModuleMixin.get_children


def patched_get_children(self, usage_key_filter=None):
    """Emulate system tools that mask courseware not visible to students"""
    def iter_children():
        """skip children not visible to students"""
        for child in GET_CHILDREN(self, usage_key_filter=usage_key_filter):
            child._field_data_cache = {}  # pylint: disable=protected-access
            if not child.visible_to_staff_only:
                yield child
    return list(iter_children())


@attr(shard=1)
@override_settings(
    XBLOCK_FIELD_DATA_WRAPPERS=['lms.djangoapps.courseware.field_overrides:OverrideModulestoreFieldData.wrap'],
    MODULESTORE_FIELD_OVERRIDE_PROVIDERS=['ccx.overrides.CustomCoursesForEdxOverrideProvider'],
)
@patch('xmodule.x_module.XModuleMixin.get_children', patched_get_children, spec=True)
class TestCCXGrades(FieldOverrideTestMixin, SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(TestCCXGrades, cls).setUpClass()
        cls._course = course = CourseFactory.create(enable_ccx=True)

        # Create a course outline
        cls.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC
        )
        chapter = ItemFactory.create(
            start=start, parent=course, category='sequential'
        )
        cls.sections = sections = [
            ItemFactory.create(
                parent=chapter,
                category="sequential",
                metadata={'graded': True, 'format': 'Homework'})
            for _ in xrange(4)
        ]
        # making problems available at class level for possible future use in tests
        cls.problems = [
            [
                ItemFactory.create(
                    parent=section,
                    category="problem",
                    data=StringResponseXMLFactory().build_xml(answer='foo'),
                    metadata={'rerandomize': 'always'}
                ) for _ in xrange(4)
            ] for section in sections
        ]

    def setUp(self):
        """
        Set up tests
        """
        super(TestCCXGrades, self).setUp()

        # Create instructor account
        self.coach = coach = AdminFactory.create()
        self.client.login(username=coach.username, password="test")

        # Create CCX
        role = CourseCcxCoachRole(self._course.id)
        role.add_users(coach)
        ccx = CcxFactory(course_id=self._course.id, coach=self.coach)

        # override course grading policy and make last section invisible to students
        override_field_for_ccx(ccx, self._course, 'grading_policy', {
            'GRADER': [
                {'drop_count': 0,
                 'min_count': 2,
                 'short_label': 'HW',
                 'type': 'Homework',
                 'weight': 1}
            ],
            'GRADE_CUTOFFS': {'Pass': 0.75},
        })
        override_field_for_ccx(
            ccx, self.sections[-1], 'visible_to_staff_only', True
        )

        # create a ccx locator and retrieve the course structure using that key
        # which emulates how a student would get access.
        self.ccx_key = CCXLocator.from_course_locator(self._course.id, unicode(ccx.id))
        self.course = get_course_by_id(self.ccx_key, depth=None)
        setup_students_and_grades(self)
        self.client.login(username=coach.username, password="test")
        self.addCleanup(RequestCache.clear_request_cache)
        from xmodule.modulestore.django import SignalHandler

        # using CCX object as sender here.
        SignalHandler.course_published.send(
            sender=ccx,
            course_key=self.ccx_key
        )

    @patch('ccx.views.render_to_response', intercept_renderer)
    @patch('instructor.views.gradebook_api.MAX_STUDENTS_PER_PAGE_GRADE_BOOK', 1)
    def test_gradebook(self):
        self.course.enable_ccx = True
        RequestCache.clear_request_cache()

        url = reverse(
            'ccx_gradebook',
            kwargs={'course_id': self.ccx_key}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Max number of student per page is one.  Patched setting MAX_STUDENTS_PER_PAGE_GRADE_BOOK = 1
        self.assertEqual(len(response.mako_context['students']), 1)  # pylint: disable=no-member
        student_info = response.mako_context['students'][0]  # pylint: disable=no-member
        self.assertEqual(student_info['grade_summary']['percent'], 0.5)
        self.assertEqual(
            student_info['grade_summary']['grade_breakdown'][0]['percent'],
            0.5)
        self.assertEqual(
            len(student_info['grade_summary']['section_breakdown']), 4)

    def test_grades_csv(self):
        self.course.enable_ccx = True
        RequestCache.clear_request_cache()

        url = reverse(
            'ccx_grades_csv',
            kwargs={'course_id': self.ccx_key}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Are the grades downloaded as an attachment?
        self.assertEqual(
            response['content-disposition'],
            'attachment'
        )
        rows = response.content.strip().split('\r')
        headers = rows[0]

        # picking first student records
        data = dict(zip(headers.strip().split(','), rows[1].strip().split(',')))
        self.assertNotIn('HW 04', data)
        self.assertEqual(data['HW 01'], '0.75')
        self.assertEqual(data['HW 02'], '0.5')
        self.assertEqual(data['HW 03'], '0.25')
        self.assertEqual(data['HW Avg'], '0.5')

    @patch('courseware.views.views.render_to_response', intercept_renderer)
    def test_student_progress(self):
        self.course.enable_ccx = True
        patch_context = patch('courseware.views.views.get_course_with_access')
        get_course = patch_context.start()
        get_course.return_value = self.course
        self.addCleanup(patch_context.stop)

        self.client.login(username=self.student.username, password="test")
        url = reverse(
            'progress',
            kwargs={'course_id': self.ccx_key}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        grades = response.mako_context['grade_summary']  # pylint: disable=no-member
        self.assertEqual(grades['percent'], 0.5)
        self.assertEqual(grades['grade_breakdown'][0]['percent'], 0.5)
        self.assertEqual(len(grades['section_breakdown']), 4)


@ddt.ddt
class CCXCoachTabTestCase(CcxTestCase):
    """
    Test case for CCX coach tab.
    """
    @classmethod
    def setUpClass(cls):
        super(CCXCoachTabTestCase, cls).setUpClass()
        cls.ccx_enabled_course = CourseFactory.create(enable_ccx=True)
        cls.ccx_disabled_course = CourseFactory.create(enable_ccx=False)

    def setUp(self):
        super(CCXCoachTabTestCase, self).setUp()
        self.user = UserFactory.create()
        for course in [self.ccx_enabled_course, self.ccx_disabled_course]:
            CourseEnrollmentFactory.create(user=self.user, course_id=course.id)
            role = CourseCcxCoachRole(course.id)
            role.add_users(self.user)

    def check_ccx_tab(self, course, user):
        """Helper function for verifying the ccx tab."""
        request = RequestFactory().request()
        request.user = user
        all_tabs = get_course_tab_list(request, course)
        return any(tab.type == 'ccx_coach' for tab in all_tabs)

    @ddt.data(
        (True, True, True),
        (True, False, False),
        (False, True, False),
        (False, False, False),
        (True, None, False)
    )
    @ddt.unpack
    def test_coach_tab_for_ccx_advance_settings(self, ccx_feature_flag, enable_ccx, expected_result):
        """
        Test ccx coach tab state (visible or hidden) depending on the value of enable_ccx flag, ccx feature flag.
        """
        with self.settings(FEATURES={'CUSTOM_COURSES_EDX': ccx_feature_flag}):
            course = self.ccx_enabled_course if enable_ccx else self.ccx_disabled_course
            self.assertEquals(
                expected_result,
                self.check_ccx_tab(course, self.user)
            )

    def test_ccx_tab_visibility_for_staff_when_not_coach_master_course(self):
        """
        Staff cannot view ccx coach dashboard on master course by default.
        """
        staff = self.make_staff()
        self.assertFalse(self.check_ccx_tab(self.course, staff))

    def test_ccx_tab_visibility_for_staff_when_coach_master_course(self):
        """
        Staff can view ccx coach dashboard only if he is coach on master course.
        """
        staff = self.make_staff()
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(staff)
        self.assertTrue(self.check_ccx_tab(self.course, staff))

    def test_ccx_tab_visibility_for_staff_ccx_course(self):
        """
        Staff can access coach dashboard on ccx course.
        """
        self.make_coach()
        ccx = self.make_ccx()
        ccx_key = CCXLocator.from_course_locator(self.course.id, unicode(ccx.id))
        staff = self.make_staff()

        with ccx_course(ccx_key) as course_ccx:
            allow_access(course_ccx, staff, 'staff')
            self.assertTrue(self.check_ccx_tab(course_ccx, staff))

    def test_ccx_tab_visibility_for_instructor_when_not_coach_master_course(self):
        """
        Instructor cannot view ccx coach dashboard on master course by default.
        """
        instructor = self.make_instructor()
        self.assertFalse(self.check_ccx_tab(self.course, instructor))

    def test_ccx_tab_visibility_for_instructor_when_coach_master_course(self):
        """
        Instructor can view ccx coach dashboard only if he is coach on master course.
        """
        instructor = self.make_instructor()
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(instructor)
        self.assertTrue(self.check_ccx_tab(self.course, instructor))

    def test_ccx_tab_visibility_for_instructor_ccx_course(self):
        """
        Instructor can access coach dashboard on ccx course.
        """
        self.make_coach()
        ccx = self.make_ccx()
        ccx_key = CCXLocator.from_course_locator(self.course.id, unicode(ccx.id))
        instructor = self.make_instructor()

        with ccx_course(ccx_key) as course_ccx:
            allow_access(course_ccx, instructor, 'instructor')
            self.assertTrue(self.check_ccx_tab(course_ccx, instructor))


class TestStudentViewsWithCCX(ModuleStoreTestCase):
    """
    Test to ensure that the student dashboard and courseware works for users enrolled in CCX
    courses.
    """

    def setUp(self):
        """
        Set up courses and enrollments.
        """
        super(TestStudentViewsWithCCX, self).setUp()

        # Create a Draft Mongo and a Split Mongo course and enroll a student user in them.
        self.student_password = "foobar"
        self.student = UserFactory.create(username="test", password=self.student_password, is_staff=False)
        self.draft_course = SampleCourseFactory.create(default_store=ModuleStoreEnum.Type.mongo)
        self.split_course = SampleCourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        CourseEnrollment.enroll(self.student, self.draft_course.id)
        CourseEnrollment.enroll(self.student, self.split_course.id)

        # Create a CCX coach.
        self.coach = AdminFactory.create()
        role = CourseCcxCoachRole(self.split_course.id)
        role.add_users(self.coach)

        # Create a CCX course and enroll the user in it.
        self.ccx = CcxFactory(course_id=self.split_course.id, coach=self.coach)
        last_week = datetime.datetime.now(UTC()) - datetime.timedelta(days=7)
        override_field_for_ccx(self.ccx, self.split_course, 'start', last_week)  # Required by self.ccx.has_started().
        self.ccx_course_key = CCXLocator.from_course_locator(self.split_course.id, self.ccx.id)
        CourseEnrollment.enroll(self.student, self.ccx_course_key)

    def test_load_student_dashboard(self):
        self.client.login(username=self.student.username, password=self.student_password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('Test CCX', response.content))

    def test_load_courseware(self):
        self.client.login(username=self.student.username, password=self.student_password)
        response = self.client.get(reverse('courseware', kwargs={'course_id': unicode(self.ccx_course_key)}))
        self.assertEqual(response.status_code, 200)
