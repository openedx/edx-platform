import datetime
import json
import re
import pytz
from mock import patch

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware.field_overrides import OverrideFieldData
from courseware.tests.factories import StudentModuleFactory
from courseware.tests.helpers import LoginEnrollmentTestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from edxmako.shortcuts import render_to_response
from student.roles import CoursePocCoachRole
from student.tests.factories import (
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import (
    CourseFactory,
    ItemFactory,
)
from ..models import (
    PersonalOnlineCourse,
    PocMembership,
    PocFutureMembership,
)
from ..overrides import get_override_for_poc, override_field_for_poc
from .factories import (
    PocFactory,
    PocMembershipFactory,
    PocFutureMembershipFactory,
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
    Tests for Personal Online Courses views.
    """
    def setUp(self):
        """
        Set up tests
        """
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
            [ItemFactory.create(parent=chapter) for _ in xrange(2)]
            for chapter in chapters])
        verticals = flatten([
            [ItemFactory.create(due=due, parent=sequential) for _ in xrange(2)]
            for sequential in sequentials])
        blocks = flatten([
            [ItemFactory.create(parent=vertical) for _ in xrange(2)]
            for vertical in verticals])

    def make_coach(self):
        role = CoursePocCoachRole(self.course.id)
        role.add_users(self.coach)

    def make_poc(self):
        poc = PocFactory(course_id=self.course.id, coach=self.coach)
        return poc

    def get_outbox(self):
        from django.core import mail
        return mail.outbox

    def tearDown(self):
        """
        Undo patches.
        """
        patch.stopall()

    def test_not_a_coach(self):
        """
        User is not a coach, should get Forbidden response.
        """
        url = reverse(
            'poc_coach_dashboard',
            kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_no_poc_created(self):
        """
        No POC is created, coach should see form to add a POC.
        """
        self.make_coach()
        url = reverse(
            'poc_coach_dashboard',
            kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search(
            '<form action=".+create_poc"',
            response.content))

    def test_create_poc(self):
        """
        Create POC. Follow redirect to coach dashboard, confirm we see
        the coach dashboard for the new POC.
        """
        self.make_coach()
        url = reverse(
            'create_poc',
            kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.post(url, {'name': 'New POC'})
        self.assertEqual(response.status_code, 302)
        url = response.get('location')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('id="poc-schedule"', response.content))

    @patch('pocs.views.render_to_response', intercept_renderer)
    @patch('pocs.views.today')
    def test_edit_schedule(self, today):
        """
        Get POC schedule, modify it, save it.
        """
        today.return_value = datetime.datetime(2014, 11, 25, tzinfo=pytz.UTC)
        self.test_create_poc()
        url = reverse(
            'poc_coach_dashboard',
            kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)
        schedule = json.loads(response.mako_context['schedule'])
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
            'save_poc',
            kwargs={'course_id': self.course.id.to_deprecated_string()})

        schedule[0]['hidden'] = False
        schedule[0]['start'] = u'2014-11-20 00:00'
        schedule[0]['children'][0]['due'] = u'2014-12-25 00:00'  # what a jerk!
        response = self.client.post(
            url, json.dumps(schedule), content_type='application/json'
        )

        schedule = json.loads(response.content)
        self.assertEqual(schedule[0]['hidden'], False)
        self.assertEqual(schedule[0]['start'], u'2014-11-20 00:00')
        self.assertEqual(
            schedule[0]['children'][0]['due'], u'2014-12-25 00:00'
        )

        # Make sure start date set on course, follows start date of earliest
        # scheduled chapter
        poc = PersonalOnlineCourse.objects.get()
        course_start = get_override_for_poc(poc, self.course, 'start')
        self.assertEqual(str(course_start)[:-9], u'2014-11-20 00:00')

    def test_enroll_member_student(self):
        """enroll a list of students who are members of the class
        """
        self.make_coach()
        poc = self.make_poc()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(len(outbox), 0)

        url = reverse(
            'poc_invite',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        data = {
            'enrollment-button': 'Enroll',
            'student-ids': u','.join([student.email, ]),
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(student.email in outbox[0].recipients())
        # a PocMembership exists for this student
        self.assertTrue(
            PocMembership.objects.filter(poc=poc, student=student).exists()
        )

    def test_unenroll_member_student(self):
        """unenroll a list of students who are members of the class
        """
        self.make_coach()
        poc = self.make_poc()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        outbox = self.get_outbox()
        self.assertEqual(len(outbox), 0)
        # student is member of POC:
        PocMembershipFactory(poc=poc, student=student)

        url = reverse(
            'poc_invite',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        data = {
            'enrollment-button': 'Unenroll',
            'student-ids': u','.join([student.email, ]),
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(student.email in outbox[0].recipients())
        # the membership for this student is gone
        self.assertFalse(
            PocMembership.objects.filter(poc=poc, student=student).exists()
        )

    def test_enroll_non_user_student(self):
        """enroll a list of students who are not users yet
        """
        test_email = "nobody@nowhere.com"
        self.make_coach()
        poc = self.make_poc()
        outbox = self.get_outbox()
        self.assertEqual(len(outbox), 0)

        url = reverse(
            'poc_invite',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        data = {
            'enrollment-button': 'Enroll',
            'student-ids': u','.join([test_email, ]),
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(test_email in outbox[0].recipients())
        self.assertTrue(
            PocFutureMembership.objects.filter(
                poc=poc, email=test_email
            ).exists()
        )

    def test_unenroll_non_user_student(self):
        """unenroll a list of students who are not users yet
        """
        test_email = "nobody@nowhere.com"
        self.make_coach()
        poc = self.make_poc()
        outbox = self.get_outbox()
        PocFutureMembershipFactory(poc=poc, email=test_email)
        self.assertEqual(len(outbox), 0)

        url = reverse(
            'poc_invite',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        data = {
            'enrollment-button': 'Unenroll',
            'student-ids': u','.join([test_email, ]),
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 1)
        self.assertTrue(test_email in outbox[0].recipients())
        self.assertFalse(
            PocFutureMembership.objects.filter(
                poc=poc, email=test_email
            ).exists()
        )

    def test_manage_add_single_student(self):
        """enroll a single student who is a member of the class already
        """
        self.make_coach()
        poc = self.make_poc()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        # no emails have been sent so far
        outbox = self.get_outbox()
        self.assertEqual(len(outbox), 0)

        url = reverse(
            'poc_manage_student',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        data = {
            'student-action': 'add',
            'student-id': u','.join([student.email, ]),
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 0)
        # a PocMembership exists for this student
        self.assertTrue(
            PocMembership.objects.filter(poc=poc, student=student).exists()
        )

    def test_manage_remove_single_student(self):
        """unenroll a single student who is a member of the class already
        """
        self.make_coach()
        poc = self.make_poc()
        enrollment = CourseEnrollmentFactory(course_id=self.course.id)
        student = enrollment.user
        PocMembershipFactory(poc=poc, student=student)
        # no emails have been sent so far
        outbox = self.get_outbox()
        self.assertEqual(len(outbox), 0)

        url = reverse(
            'poc_manage_student',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        data = {
            'student-action': 'revoke',
            'student-id': u','.join([student.email, ]),
        }
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        # we were redirected to our current location
        self.assertEqual(len(response.redirect_chain), 1)
        self.assertTrue(302 in response.redirect_chain[0])
        self.assertEqual(len(outbox), 0)
        # a PocMembership exists for this student
        self.assertFalse(
            PocMembership.objects.filter(poc=poc, student=student).exists()
        )


@override_settings(FIELD_OVERRIDE_PROVIDERS=(
    'pocs.overrides.PersonalOnlineCoursesOverrideProvider',))
class TestPocGrades(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for Personal Online Courses views.
    """
    def setUp(self):
        """
        Set up tests
        """
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

        role = CoursePocCoachRole(self.course.id)
        role.add_users(coach)
        self.poc = poc = PocFactory(course_id=self.course.id, coach=self.coach)

        self.student = student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
        PocMembershipFactory(poc=poc, student=student, active=True)

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
            block._field_data = OverrideFieldData.wrap(  # pylint: disable=protected-access
                coach, block._field_data)  # pylint: disable=protected-access
            block._field_data_cache = {}
            visible_children(block)

        patch_context = patch('pocs.views.get_course_by_id')
        get_course = patch_context.start()
        get_course.return_value = course
        self.addCleanup(patch_context.stop)

        override_field_for_poc(poc, course, 'grading_policy', {
            'GRADER': [
                {'drop_count': 0,
                 'min_count': 2,
                 'short_label': 'HW',
                 'type': 'Homework',
                 'weight': 1}
            ],
            'GRADE_CUTOFFS': {'Pass': 0.75},
        })
        override_field_for_poc(
            poc, sections[-1], 'visible_to_staff_only', True)

    @patch('pocs.views.render_to_response', intercept_renderer)
    def test_gradebook(self):
        url = reverse(
            'poc_gradebook',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        student_info = response.mako_context['students'][0]
        self.assertEqual(student_info['grade_summary']['percent'], 0.5)
        self.assertEqual(
            student_info['grade_summary']['grade_breakdown'][0]['percent'],
            0.5)
        self.assertEqual(
            len(student_info['grade_summary']['section_breakdown']), 4)

    def test_grades_csv(self):
        url = reverse(
            'poc_grades_csv',
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
        url = reverse(
            'progress',
            kwargs={'course_id': self.course.id.to_deprecated_string()}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        grades = response.mako_context['grade_summary']
        self.assertEqual(grades['percent'], 0.5)
        self.assertEqual(grades['grade_breakdown'][0]['percent'], 0.5)
        self.assertEqual(len(grades['section_breakdown']), 4)


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
        yield block
        for child in block.get_children():
            for descendant in visit(child):  # wish they'd backport yield from
                yield descendant
    return visit(course)


def visible_children(block):
    block_get_children = block.get_children

    def get_children():
        def iter_children():
            for child in block_get_children():
                child._field_data_cache = {}
                if not child.visible_to_staff_only:
                    yield child
        return list(iter_children())
    block.get_children = get_children
