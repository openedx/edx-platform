import datetime
import json
import re
import pytz
from mock import patch

from courseware.tests.helpers import LoginEnrollmentTestCase
from django.core.urlresolvers import reverse
from edxmako.shortcuts import render_to_response
from student.roles import CoursePocCoachRole
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from ..models import PersonalOnlineCourse
from ..overrides import get_override_for_poc


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


def flatten(seq):
    """
    For [[1, 2], [3, 4]] returns [1, 2, 3, 4].  Does not recurse.
    """
    return [x for sub in seq for x in sub]
