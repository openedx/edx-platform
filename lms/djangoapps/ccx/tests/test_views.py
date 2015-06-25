"""
test views
"""
import datetime
import json
import re
import pytz
from mock import patch

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware.field_overrides import OverrideFieldData  # pylint: disable=import-error
from courseware.tests.factories import StudentModuleFactory  # pylint: disable=import-error
from courseware.tests.helpers import LoginEnrollmentTestCase  # pylint: disable=import-error
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from edxmako.shortcuts import render_to_response  # pylint: disable=import-error
from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
from student.tests.factories import (  # pylint: disable=import-error
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)

from xmodule.x_module import XModuleMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    ItemFactory,
)
from ..models import (
    CustomCourseForEdX,
    CcxMembership,
    CcxFutureMembership,
)
from ..overrides import get_override_for_ccx, override_field_for_ccx
from .. import ACTIVE_CCX_KEY
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


class TestCoachDashboard(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """
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

    def tearDown(self):
        """
        Undo patches.
        """
        super(TestCoachDashboard, self).tearDown()
        patch.stopall()

    def test_not_a_coach(self):
        """
        User is not a coach, should get Forbidden response.
        """
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': self.course.id.to_deprecated_string()})
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
        self.test_create_ccx()
        url = reverse(
            'ccx_coach_dashboard',
            kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)
        schedule = json.loads(response.mako_context['schedule'])  # pylint: disable=no-member
        self.assertEqual(len(schedule), 2)
        self.assertEqual(schedule[0]['hidden'], True)
        self.assertEqual(schedule[0]['start'], None)
        self.assertEqual(schedule[0]['children'][0]['start'], None)
        self.assertEqual(schedule[0]['due'], None)
        self.assertEqual(schedule[0]['children'][0]['due'], None)
        self.assertEqual(
            schedule[0]['children'][0]['children'][0]['due'], None
        )

        url = reverse(
            'save_ccx',
            kwargs={'course_id': self.course.id.to_deprecated_string()})

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
        self.assertEqual(policy['GRADER'][0]['min_count'], 4)
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
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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


def patched_get_children(self, usage_key_filter=None):  # pylint: disable=missing-docstring
    def iter_children():  # pylint: disable=missing-docstring
        print self.__dict__
        for child in GET_CHILDREN(self, usage_key_filter=usage_key_filter):
            child._field_data_cache = {}  # pylint: disable=protected-access
            if not child.visible_to_staff_only:
                yield child
    return list(iter_children())


@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'ccx.overrides.CustomCoursesForEdxOverrideProvider',))
@patch('xmodule.x_module.XModuleMixin.get_children', patched_get_children, spec=True)
class TestCCXGrades(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for Custom Courses views.
    """
    def setUp(self):
        """
        Set up tests
        """
        super(TestCCXGrades, self).setUp()
        self.course = course = CourseFactory.create()

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

        role = CourseCcxCoachRole(self.course.id)
        role.add_users(coach)
        self.ccx = ccx = CcxFactory(course_id=self.course.id, coach=self.coach)

        self.student = student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
        CcxMembershipFactory(ccx=ccx, student=student, active=True)

        for i, section in enumerate(sections):
            for j in xrange(4):
                item = ItemFactory.create(
                    parent=section,
                    category="problem",
                    data=StringResponseXMLFactory().build_xml(answer='foo'),
                    metadata={'rerandomize': 'always'}
                )

                StudentModuleFactory.create(
                    grade=1 if i < j else 0,
                    max_grade=1,
                    student=student,
                    course_id=self.course.id,
                    module_state_key=item.location
                )

        # Apparently the test harness doesn't use LmsFieldStorage, and I'm not
        # sure if there's a way to poke the test harness to do so.  So, we'll
        # just inject the override field storage in this brute force manner.
        OverrideFieldData.provider_classes = None
        for block in iter_blocks(course):
            block._field_data = OverrideFieldData.wrap(   # pylint: disable=protected-access
                coach, block._field_data)   # pylint: disable=protected-access
            block._field_data_cache = {'tabs': [], 'discussion_topics': []}  # pylint: disable=protected-access

        def cleanup_provider_classes():
            """
            After everything is done, clean up by un-doing the change to the
            OverrideFieldData object that is done during the wrap method.
            """
            OverrideFieldData.provider_classes = None
        self.addCleanup(cleanup_provider_classes)

        patch_context = patch('ccx.views.get_course_by_id')
        get_course = patch_context.start()
        get_course.return_value = course
        self.addCleanup(patch_context.stop)

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

    @patch('ccx.views.render_to_response', intercept_renderer)
    def test_gradebook(self):
        url = reverse(
            'ccx_gradebook',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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
        url = reverse(
            'ccx_grades_csv',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
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
        patch_context = patch('courseware.views.get_course_with_access')
        get_course = patch_context.start()
        get_course.return_value = self.course
        self.addCleanup(patch_context.stop)

        self.client.login(username=self.student.username, password="test")
        session = self.client.session
        session[ACTIVE_CCX_KEY] = self.ccx.id  # pylint: disable=no-member
        session.save()
        self.client.session.get(ACTIVE_CCX_KEY)
        url = reverse(
            'progress',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        grades = response.mako_context['grade_summary']  # pylint: disable=no-member
        self.assertEqual(grades['percent'], 0.5)
        self.assertEqual(grades['grade_breakdown'][0]['percent'], 0.5)
        self.assertEqual(len(grades['section_breakdown']), 4)


class TestSwitchActiveCCX(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """Verify the view for switching which CCX is active, if any
    """
    def setUp(self):
        super(TestSwitchActiveCCX, self).setUp()
        self.course = course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)
        enrollment = CourseEnrollmentFactory.create(course_id=course.id)
        self.user = enrollment.user
        self.target_url = reverse(
            'course_root', args=[course.id.to_deprecated_string()]
        )

    def register_user_in_ccx(self, active=False):
        """create registration of self.user in self.ccx

        registration will be inactive unless active=True
        """
        CcxMembershipFactory(ccx=self.ccx, student=self.user, active=active)

    def revoke_ccx_registration(self):
        """
        delete membership
        """
        membership = CcxMembership.objects.filter(
            ccx=self.ccx, student=self.user
        )
        membership.delete()

    def verify_active_ccx(self, request, id=None):  # pylint: disable=redefined-builtin, invalid-name
        """verify that we have the correct active ccx"""
        if id:
            id = str(id)
        self.assertEqual(id, request.session.get(ACTIVE_CCX_KEY, None))

    def test_unauthorized_cannot_switch_to_ccx(self):
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string(), self.ccx.id]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)

    def test_unauthorized_cannot_switch_to_mooc(self):
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string()]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)

    def test_enrolled_inactive_user_cannot_select_ccx(self):
        self.register_user_in_ccx(active=False)
        self.client.login(username=self.user.username, password="test")
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string(), self.ccx.id]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.get('Location', '').endswith(self.target_url))  # pylint: disable=no-member
        # if the ccx were active, we'd need to pass the ID of the ccx here.
        self.verify_active_ccx(self.client)

    def test_enrolled_user_can_select_ccx(self):
        self.register_user_in_ccx(active=True)
        self.client.login(username=self.user.username, password="test")
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string(), self.ccx.id]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.get('Location', '').endswith(self.target_url))  # pylint: disable=no-member
        self.verify_active_ccx(self.client, self.ccx.id)

    def test_enrolled_user_can_select_mooc(self):
        self.register_user_in_ccx(active=True)
        self.client.login(username=self.user.username, password="test")
        # pre-seed the session with the ccx id
        session = self.client.session
        session[ACTIVE_CCX_KEY] = str(self.ccx.id)
        session.save()
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string()]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.get('Location', '').endswith(self.target_url))  # pylint: disable=no-member
        self.verify_active_ccx(self.client)

    def test_unenrolled_user_cannot_select_ccx(self):
        self.client.login(username=self.user.username, password="test")
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string(), self.ccx.id]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.get('Location', '').endswith(self.target_url))  # pylint: disable=no-member
        # if the ccx were active, we'd need to pass the ID of the ccx here.
        self.verify_active_ccx(self.client)

    def test_unenrolled_user_switched_to_mooc(self):
        self.client.login(username=self.user.username, password="test")
        # pre-seed the session with the ccx id
        session = self.client.session
        session[ACTIVE_CCX_KEY] = str(self.ccx.id)
        session.save()
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string(), self.ccx.id]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.get('Location', '').endswith(self.target_url))  # pylint: disable=no-member
        # we tried to select the ccx but are not registered, so we are switched
        # back to the mooc view
        self.verify_active_ccx(self.client)

    def test_unassociated_course_and_ccx_not_selected(self):
        new_course = CourseFactory.create()
        self.client.login(username=self.user.username, password="test")
        expected_url = reverse(
            'course_root', args=[new_course.id.to_deprecated_string()]
        )
        # the ccx and the course are not related.
        switch_url = reverse(
            'switch_active_ccx',
            args=[new_course.id.to_deprecated_string(), self.ccx.id]
        )
        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.get('Location', '').endswith(expected_url))  # pylint: disable=no-member
        # the mooc should be active
        self.verify_active_ccx(self.client)

    def test_missing_ccx_cannot_be_selected(self):
        self.register_user_in_ccx()
        self.client.login(username=self.user.username, password="test")
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string(), self.ccx.id]
        )
        # delete the ccx
        self.ccx.delete()  # pylint: disable=no-member

        response = self.client.get(switch_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.get('Location', '').endswith(self.target_url))  # pylint: disable=no-member
        # we tried to select the ccx it doesn't exist anymore, so we are
        # switched back to the mooc view
        self.verify_active_ccx(self.client)

    def test_revoking_ccx_membership_revokes_active_ccx(self):
        self.register_user_in_ccx(active=True)
        self.client.login(username=self.user.username, password="test")
        # ensure ccx is active in the request session
        switch_url = reverse(
            'switch_active_ccx',
            args=[self.course.id.to_deprecated_string(), self.ccx.id]
        )
        self.client.get(switch_url)
        self.verify_active_ccx(self.client, self.ccx.id)
        # unenroll the user from the ccx
        self.revoke_ccx_registration()
        # request the course root and verify that the ccx is not active
        self.client.get(self.target_url)
        self.verify_active_ccx(self.client)


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
