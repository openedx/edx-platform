"""
test views
"""
import datetime
import json
import re
import pytz
import ddt
import urlparse
from mock import patch, MagicMock
from nose.plugins.attrib import attr

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware.courses import get_course_by_id
from courseware.tests.factories import StudentModuleFactory
from courseware.tests.helpers import LoginEnrollmentTestCase
from courseware.tabs import get_course_tab_list
from django.core.urlresolvers import reverse, resolve
from django.utils.timezone import UTC
from django.test.utils import override_settings
from django.test import RequestFactory
from edxmako.shortcuts import render_to_response
from request_cache.middleware import RequestCache
from opaque_keys.edx.keys import CourseKey
from student.roles import CourseCcxCoachRole
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
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    SharedModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    ItemFactory,
)
from ccx_keys.locator import CCXLocator

from ..models import (
    CustomCourseForEdX,
)
from ..overrides import get_override_for_ccx, override_field_for_ccx
from .factories import (
    CcxFactory,
)


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


@attr('shard_1')
@ddt.ddt
class TestCoachDashboard(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    @classmethod
    def setUpClass(cls):
        super(TestCoachDashboard, cls).setUpClass()
        cls.course = course = CourseFactory.create()

        # Create a course outline
        cls.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC
        )
        cls.mooc_due = due = datetime.datetime(
            2010, 7, 7, 0, 0, tzinfo=pytz.UTC
        )

        cls.chapters = [
            ItemFactory.create(start=start, parent=course) for _ in xrange(2)
        ]
        cls.sequentials = flatten([
            [
                ItemFactory.create(parent=chapter) for _ in xrange(2)
            ] for chapter in cls.chapters
        ])
        cls.verticals = flatten([
            [
                ItemFactory.create(
                    due=due, parent=sequential, graded=True, format='Homework'
                ) for _ in xrange(2)
            ] for sequential in cls.sequentials
        ])

        # Trying to wrap the whole thing in a bulk operation fails because it
        # doesn't find the parents. But we can at least wrap this part...
        with cls.store.bulk_operations(course.id, emit_signals=False):
            blocks = flatten([  # pylint: disable=unused-variable
                [
                    ItemFactory.create(parent=vertical) for _ in xrange(2)
                ] for vertical in cls.verticals
            ])

    def setUp(self):
        """
        Set up tests
        """
        super(TestCoachDashboard, self).setUp()

        # Create instructor account
        self.coach = coach = AdminFactory.create()
        self.client.login(username=coach.username, password="test")
        # create an instance of modulestore
        self.mstore = modulestore()

    def make_coach(self):
        """
        create coach user
        """
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(self.coach)

    def make_ccx(self):
        """
        create ccx
        """
        ccx = CcxFactory(course_id=self.course.id, coach=self.coach)
        return ccx

    def get_outbox(self):
        """
        get fake outbox
        """
        from django.core import mail
        return mail.outbox

    def assert_elements_in_schedule(self, url, n_chapters=2, n_sequentials=4, n_verticals=8):
        """
        Helper function to count visible elements in the schedule
        """
        response = self.client.get(url)
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

    def test_not_a_coach(self):
        """
        User is not a coach, should get Forbidden response.
        """
        ccx = self.make_ccx()
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

    def test_create_ccx(self):
        """
        Create CCX. Follow redirect to coach dashboard, confirm we see
        the coach dashboard for the new CCX.
        """

        self.make_coach()
        url = reverse(
            'create_ccx',
            kwargs={'course_id': unicode(self.course.id)})

        response = self.client.post(url, {'name': 'New CCX'})
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

    @SharedModuleStoreTestCase.modifies_courseware
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
        self.assertEqual(schedule[0]['start'], None)
        self.assertEqual(schedule[0]['children'][0]['start'], None)
        self.assertEqual(schedule[0]['due'], None)
        self.assertEqual(schedule[0]['children'][0]['due'], None)
        self.assertEqual(
            schedule[0]['children'][0]['children'][0]['due'], None
        )

        url = reverse(
            'save_ccx',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)})

        def unhide(unit):
            """
            Recursively unhide a unit and all of its children in the CCX
            schedule.
            """
            unit['hidden'] = False
            for child in unit.get('children', ()):
                unhide(child)

        unhide(schedule[0])
        schedule[0]['start'] = u'2014-11-20 00:00'
        schedule[0]['children'][0]['due'] = u'2014-12-25 00:00'  # what a jerk!
        response = self.client.post(
            url, json.dumps(schedule), content_type='application/json'
        )

        schedule = json.loads(response.content)['schedule']
        self.assertEqual(schedule[0]['hidden'], False)
        self.assertEqual(schedule[0]['start'], u'2014-11-20 00:00')
        self.assertEqual(
            schedule[0]['children'][0]['due'], u'2014-12-25 00:00'
        )

        # Make sure start date set on course, follows start date of earliest
        # scheduled chapter
        ccx = CustomCourseForEdX.objects.get()
        course_start = get_override_for_ccx(ccx, self.course, 'start')
        self.assertEqual(str(course_start)[:-9], u'2014-11-20 00:00')

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

    def test_enroll_member_student(self):
        """enroll a list of students who are members of the class
        """
        self.make_coach()
        ccx = self.make_ccx()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
        )
        data = {
            'enrollment-button': 'Enroll',
            'student-ids': u','.join([student.email, ]),  # pylint: disable=no-member
            'email-students': 'Notify-students-by-email',
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertIn(student.email, outbox[0].recipients())  # pylint: disable=no-member
        # a CcxMembership exists for this student
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=self.course.id, user=student).exists()
        )

    def test_unenroll_member_student(self):
        """unenroll a list of students who are members of the class
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        enrollment = CourseEnrollmentFactory(course_id=course_key)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': course_key}
        )
        data = {
            'enrollment-button': 'Unenroll',
            'student-ids': u','.join([student.email, ]),  # pylint: disable=no-member
            'email-students': 'Notify-students-by-email',
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertIn(student.email, outbox[0].recipients())  # pylint: disable=no-member

    def test_enroll_non_user_student(self):
        """enroll a list of students who are not users yet
        """
        test_email = "nobody@nowhere.com"
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': course_key}
        )
        data = {
            'enrollment-button': 'Enroll',
            'student-ids': u','.join([test_email, ]),
            'email-students': 'Notify-students-by-email',
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertIn(test_email, outbox[0].recipients())
        self.assertTrue(
            CourseEnrollmentAllowed.objects.filter(
                course_id=course_key, email=test_email
            ).exists()
        )

    def test_unenroll_non_user_student(self):
        """unenroll a list of students who are not users yet
        """
        test_email = "nobody@nowhere.com"
        self.make_coach()
        course = CourseFactory.create()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(course.id, ccx.id)
        outbox = self.get_outbox()
        CourseEnrollmentAllowed(course_id=course_key, email=test_email)
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': course_key}
        )
        data = {
            'enrollment-button': 'Unenroll',
            'student-ids': u','.join([test_email, ]),
            'email-students': 'Notify-students-by-email',
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertFalse(
            CourseEnrollmentAllowed.objects.filter(
                course_id=course_key, email=test_email
            ).exists()
        )

    @ddt.data("dummy_student_id", "xyz@gmail.com")
    def test_manage_add_single_invalid_student(self, student_id):
        """enroll a single non valid student
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        url = reverse(
            'ccx_manage_student',
            kwargs={'course_id': course_key}
        )
        redirect_url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': course_key}
        )
        data = {
            'student-action': 'add',
            'student-id': u','.join([student_id, ]),  # pylint: disable=no-member
        }
        response = self.client.post(url, data=data, follow=True)

        error_message = 'Could not find a user with name or email "{student_id}" '.format(
            student_id=student_id
        )
        self.assertContains(response, error_message, status_code=200)

        # we were redirected to our current location
        self.assertRedirects(response, redirect_url, status_code=302)

    def test_manage_add_single_student(self):
        """enroll a single student who is a member of the class already
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        enrollment = CourseEnrollmentFactory(course_id=course_key)
        student = enrollment.user
        # no emails have been sent so far
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_manage_student',
            kwargs={'course_id': course_key}
        )
        data = {
            'student-action': 'add',
            'student-id': u','.join([student.email, ]),  # pylint: disable=no-member
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(outbox, [])
        # a CcxMembership exists for this student
        self.assertTrue(
            CourseEnrollment.objects.filter(course_id=course_key, user=student).exists()
        )

    def test_manage_remove_single_student(self):
        """unenroll a single student who is a member of the class already
        """
        self.make_coach()
        ccx = self.make_ccx()
        course_key = CCXLocator.from_course_locator(self.course.id, ccx.id)
        enrollment = CourseEnrollmentFactory(course_id=course_key)
        student = enrollment.user
        # no emails have been sent so far
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_manage_student',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
        )
        data = {
            'student-action': 'revoke',
            'student-id': u','.join([student.email, ]),  # pylint: disable=no-member
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertIn(302, response.redirect_chain[0])
        self.assertEqual(outbox, [])


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


@attr('shard_1')
@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'ccx.overrides.CustomCoursesForEdxOverrideProvider',))
@patch('xmodule.x_module.XModuleMixin.get_children', patched_get_children, spec=True)
class TestCCXGrades(SharedModuleStoreTestCase, LoginEnrollmentTestCase):
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
        self.ccx_key = CCXLocator.from_course_locator(self._course.id, ccx.id)
        self.course = get_course_by_id(self.ccx_key, depth=None)

        self.student = student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

        # create grades for self.student as if they'd submitted the ccx
        for chapter in self.course.get_children():
            for i, section in enumerate(chapter.get_children()):
                for j, problem in enumerate(section.get_children()):
                    # if not problem.visible_to_staff_only:
                    StudentModuleFactory.create(
                        grade=1 if i < j else 0,
                        max_grade=1,
                        student=self.student,
                        course_id=self.course.id,
                        module_state_key=problem.location
                    )

        self.client.login(username=coach.username, password="test")

        self.addCleanup(RequestCache.clear_request_cache)

    @patch('ccx.views.render_to_response', intercept_renderer)
    def test_gradebook(self):
        self.course.enable_ccx = True
        RequestCache.clear_request_cache()

        url = reverse(
            'ccx_gradebook',
            kwargs={'course_id': self.ccx_key}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
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

        headers, row = (
            row.strip().split(',') for row in
            response.content.strip().split('\n')
        )
        data = dict(zip(headers, row))
        self.assertNotIn('HW 04', data)
        self.assertEqual(data['HW 01'], '0.75')
        self.assertEqual(data['HW 02'], '0.5')
        self.assertEqual(data['HW 03'], '0.25')
        self.assertEqual(data['HW Avg'], '0.5')

    @patch('courseware.views.render_to_response', intercept_renderer)
    def test_student_progress(self):
        self.course.enable_ccx = True
        patch_context = patch('courseware.views.get_course_with_access')
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
class CCXCoachTabTestCase(SharedModuleStoreTestCase):
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

    def check_ccx_tab(self, course):
        """Helper function for verifying the ccx tab."""
        request = RequestFactory().request()
        request.user = self.user
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
                self.check_ccx_tab(course)
            )


class TestStudentDashboardWithCCX(ModuleStoreTestCase):
    """
    Test to ensure that the student dashboard works for users enrolled in CCX
    courses.
    """

    def setUp(self):
        """
        Set up courses and enrollments.
        """
        super(TestStudentDashboardWithCCX, self).setUp()

        # Create a Draft Mongo and a Split Mongo course and enroll a student user in them.
        self.student_password = "foobar"
        self.student = UserFactory.create(username="test", password=self.student_password, is_staff=False)
        self.draft_course = CourseFactory.create(default_store=ModuleStoreEnum.Type.mongo)
        self.split_course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
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
        course_key = CCXLocator.from_course_locator(self.split_course.id, self.ccx.id)
        CourseEnrollment.enroll(self.student, course_key)

    def test_load_student_dashboard(self):
        self.client.login(username=self.student.username, password=self.student_password)
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('Test CCX', response.content))


def flatten(seq):
    """
    For [[1, 2], [3, 4]] returns [1, 2, 3, 4].  Does not recurse.
    """
    return [x for sub in seq for x in sub]


def iter_blocks(course):
    """
    Returns an iterator over all of the blocks in a course.
    """
    def visit(block):
        """ get child blocks """
        yield block
        for child in block.get_children():
            for descendant in visit(child):  # wish they'd backport yield from
                yield descendant
    return visit(course)
