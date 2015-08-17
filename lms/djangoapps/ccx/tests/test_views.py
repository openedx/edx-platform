"""
test views
"""
import datetime
import json
import re
import pytz
import ddt
from mock import patch, MagicMock
from nose.plugins.attrib import attr

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware.courses import get_course_by_id  # pyline: disable=import-error
from courseware.field_overrides import OverrideFieldData  # pylint: disable=import-error
from courseware.tests.factories import StudentModuleFactory  # pylint: disable=import-error
from courseware.tests.helpers import LoginEnrollmentTestCase  # pylint: disable=import-error
from courseware.tabs import get_course_tab_list
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.test import RequestFactory
from edxmako.shortcuts import render_to_response  # pylint: disable=import-error
from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
from student.tests.factories import (  # pylint: disable=import-error
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)

from xmodule.x_module import XModuleMixin
from xmodule.modulestore.tests.django_utils import (
    ModuleStoreTestCase,
    TEST_DATA_SPLIT_MODULESTORE)
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    ItemFactory,
)
from ccx_keys.locator import CCXLocator

from ..models import (
    CustomCourseForEdX,
    CcxMembership,
    CcxFutureMembership,
)
from ..overrides import get_override_for_ccx, override_field_for_ccx
from .factories import (
    CcxFactory,
    CcxMembershipFactory,
    CcxFutureMembershipFactory,
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
class TestCoachDashboard(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up tests
        """
        super(TestCoachDashboard, self).setUp()
        self.course = course = CourseFactory.create()

        # Create instructor account
        self.coach = coach = AdminFactory.create()
        self.client.login(username=coach.username, password="test")

        # Create a course outline
        self.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC)
        self.mooc_due = due = datetime.datetime(
            2010, 7, 7, 0, 0, tzinfo=pytz.UTC)
        chapters = [ItemFactory.create(start=start, parent=course)
                    for _ in xrange(2)]
        sequentials = flatten([
            [
                ItemFactory.create(parent=chapter) for _ in xrange(2)
            ] for chapter in chapters
        ])
        verticals = flatten([
            [
                ItemFactory.create(
                    due=due, parent=sequential, graded=True, format='Homework'
                ) for _ in xrange(2)
            ] for sequential in sequentials
        ])
        blocks = flatten([  # pylint: disable=unused-variable
            [
                ItemFactory.create(parent=vertical) for _ in xrange(2)
            ] for vertical in verticals
        ])

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
            kwargs={'course_id': self.course.id.to_deprecated_string()})
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
            kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'name': 'New CCX'})
        self.assertEqual(response.status_code, 302)
        url = response.get('location')  # pylint: disable=no-member
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('id="ccx-schedule"', response.content))

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
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(student.email in outbox[0].recipients())  # pylint: disable=no-member
        # a CcxMembership exists for this student
        self.assertTrue(
            CcxMembership.objects.filter(ccx=ccx, student=student).exists()
        )

    def test_unenroll_member_student(self):
        """unenroll a list of students who are members of the class
        """
        self.make_coach()
        ccx = self.make_ccx()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])
        # student is member of CCX:
        CcxMembershipFactory(ccx=ccx, student=student)

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
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
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(student.email in outbox[0].recipients())  # pylint: disable=no-member
        # the membership for this student is gone
        self.assertFalse(
            CcxMembership.objects.filter(ccx=ccx, student=student).exists()
        )

    def test_enroll_non_user_student(self):
        """enroll a list of students who are not users yet
        """
        test_email = "nobody@nowhere.com"
        self.make_coach()
        ccx = self.make_ccx()
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
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
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(test_email in outbox[0].recipients())
        self.assertTrue(
            CcxFutureMembership.objects.filter(
                ccx=ccx, email=test_email
            ).exists()
        )

    def test_unenroll_non_user_student(self):
        """unenroll a list of students who are not users yet
        """
        test_email = "nobody@nowhere.com"
        self.make_coach()
        ccx = self.make_ccx()
        outbox = self.get_outbox()
        CcxFutureMembershipFactory(ccx=ccx, email=test_email)
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_invite',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
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
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(test_email in outbox[0].recipients())
        self.assertFalse(
            CcxFutureMembership.objects.filter(
                ccx=ccx, email=test_email
            ).exists()
        )

    def test_manage_add_single_student(self):
        """enroll a single student who is a member of the class already
        """
        self.make_coach()
        ccx = self.make_ccx()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        # no emails have been sent so far
        outbox = self.get_outbox()
        self.assertEqual(outbox, [])

        url = reverse(
            'ccx_manage_student',
            kwargs={'course_id': CCXLocator.from_course_locator(self.course.id, ccx.id)}
        )
        data = {
            'student-action': 'add',
            'student-id': u','.join([student.email, ]),  # pylint: disable=no-member
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(outbox, [])
        # a CcxMembership exists for this student
        self.assertTrue(
            CcxMembership.objects.filter(ccx=ccx, student=student).exists()
        )

    def test_manage_remove_single_student(self):
        """unenroll a single student who is a member of the class already
        """
        self.make_coach()
        ccx = self.make_ccx()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        CcxMembershipFactory(ccx=ccx, student=student)
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
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(outbox, [])
        # a CcxMembership exists for this student
        self.assertFalse(
            CcxMembership.objects.filter(ccx=ccx, student=student).exists()
        )


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
class TestCCXGrades(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up tests
        """
        super(TestCCXGrades, self).setUp()
        self.course = course = CourseFactory.create(enable_ccx=True)

        # Create instructor account
        self.coach = coach = AdminFactory.create()
        self.client.login(username=coach.username, password="test")

        # Create a course outline
        self.mooc_start = start = datetime.datetime(
            2010, 5, 12, 2, 42, tzinfo=pytz.UTC)
        chapter = ItemFactory.create(
            start=start, parent=course, category='sequential')
        sections = [
            ItemFactory.create(
                parent=chapter,
                category="sequential",
                metadata={'graded': True, 'format': 'Homework'})
            for _ in xrange(4)]
        # pylint: disable=unused-variable
        problems = [
            [
                ItemFactory.create(
                    parent=section,
                    category="problem",
                    data=StringResponseXMLFactory().build_xml(answer='foo'),
                    metadata={'rerandomize': 'always'}
                ) for _ in xrange(4)
            ] for section in sections
        ]

        # Create CCX
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        ccx = CcxFactory(course_id=course.id, coach=self.coach)

        # Apparently the test harness doesn't use LmsFieldStorage, and I'm not
        # sure if there's a way to poke the test harness to do so.  So, we'll
        # just inject the override field storage in this brute force manner.
        OverrideFieldData.provider_classes = None
        # pylint: disable=protected-access
        for block in iter_blocks(course):
            block._field_data = OverrideFieldData.wrap(coach, course, block._field_data)
            new_cache = {'tabs': [], 'discussion_topics': []}
            if 'grading_policy' in block._field_data_cache:
                new_cache['grading_policy'] = block._field_data_cache['grading_policy']
            block._field_data_cache = new_cache

        def cleanup_provider_classes():
            """
            After everything is done, clean up by un-doing the change to the
            OverrideFieldData object that is done during the wrap method.
            """
            OverrideFieldData.provider_classes = None
        self.addCleanup(cleanup_provider_classes)

        # override course grading policy and make last section invisible to students
        override_field_for_ccx(ccx, course, 'grading_policy', {
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
            ccx, sections[-1], 'visible_to_staff_only', True)

        # create a ccx locator and retrieve the course structure using that key
        # which emulates how a student would get access.
        self.ccx_key = CCXLocator.from_course_locator(course.id, ccx.id)
        self.course = get_course_by_id(self.ccx_key)

        self.student = student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
        CcxMembershipFactory(ccx=ccx, student=student, active=True)

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

    @patch('ccx.views.render_to_response', intercept_renderer)
    def test_gradebook(self):
        self.course.enable_ccx = True
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
        url = reverse(
            'ccx_grades_csv',
            kwargs={'course_id': self.ccx_key}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        headers, row = (
            row.strip().split(',') for row in
            response.content.strip().split('\n')
        )
        data = dict(zip(headers, row))
        self.assertEqual(data['HW 01'], '0.75')
        self.assertEqual(data['HW 02'], '0.5')
        self.assertEqual(data['HW 03'], '0.25')
        self.assertEqual(data['HW Avg'], '0.5')
        self.assertTrue('HW 04' not in data)

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
class CCXCoachTabTestCase(ModuleStoreTestCase):
    """
    Test case for CCX coach tab.
    """
    def setUp(self):
        super(CCXCoachTabTestCase, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(self.user)

    def check_ccx_tab(self):
        """Helper function for verifying the ccx tab."""
        request = RequestFactory().request()
        request.user = self.user
        all_tabs = get_course_tab_list(request, self.course)
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
            self.course.enable_ccx = enable_ccx
            self.assertEquals(
                expected_result,
                self.check_ccx_tab()
            )


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
