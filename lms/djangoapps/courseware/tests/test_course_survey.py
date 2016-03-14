"""
Python tests for the Survey workflows
"""

from collections import OrderedDict
from nose.plugins.attrib import attr
from copy import deepcopy

from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from survey.models import SurveyForm, SurveyAnswer

from common.test.utils import XssTestMixin
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.helpers import LoginEnrollmentTestCase


@attr('shard_1')
class SurveyViewsTests(LoginEnrollmentTestCase, ModuleStoreTestCase, XssTestMixin):
    """
    All tests for the views.py file
    """

    STUDENT_INFO = [('view@test.com', 'foo')]

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(SurveyViewsTests, self).setUp()

        self.test_survey_name = 'TestSurvey'
        self.test_form = '<input name="field1"></input>'

        self.survey = SurveyForm.create(self.test_survey_name, self.test_form)

        self.student_answers = OrderedDict({
            u'field1': u'value1',
            u'field2': u'value2',
        })

        self.course = CourseFactory.create(
            display_name='<script>alert("XSS")</script>',
            course_survey_required=True,
            course_survey_name=self.test_survey_name
        )

        self.course_with_bogus_survey = CourseFactory.create(
            course_survey_required=True,
            course_survey_name="DoesNotExist"
        )

        self.course_without_survey = CourseFactory.create()

        # Create student accounts and activate them.
        for i in range(len(self.STUDENT_INFO)):
            email, password = self.STUDENT_INFO[i]
            username = 'u{0}'.format(i)
            self.create_account(username, email, password)
            self.activate_user(email)

        email, password = self.STUDENT_INFO[0]
        self.login(email, password)
        self.enroll(self.course, True)
        self.enroll(self.course_without_survey, True)
        self.enroll(self.course_with_bogus_survey, True)

        self.user = User.objects.get(email=email)

        self.view_url = reverse('view_survey', args=[self.test_survey_name])
        self.postback_url = reverse('submit_answers', args=[self.test_survey_name])

    def _assert_survey_redirect(self, course):
        """
        Helper method to assert that all known redirect points do redirect as expected
        """
        for view_name in ['courseware', 'info', 'progress']:
            resp = self.client.get(
                reverse(
                    view_name,
                    kwargs={'course_id': unicode(course.id)}
                )
            )
            self.assertRedirects(
                resp,
                reverse('course_survey', kwargs={'course_id': unicode(course.id)})
            )

    def _assert_no_redirect(self, course):
        """
        Helper method to asswer that all known conditionally redirect points do
        not redirect as expected
        """
        for view_name in ['courseware', 'info', 'progress']:
            resp = self.client.get(
                reverse(
                    view_name,
                    kwargs={'course_id': unicode(course.id)}
                )
            )
            self.assertEquals(resp.status_code, 200)

    def test_visiting_course_without_survey(self):
        """
        Verifies that going to the courseware which does not have a survey does
        not redirect to a survey
        """
        self._assert_no_redirect(self.course_without_survey)

    def test_visiting_course_with_survey_redirects(self):
        """
        Verifies that going to the courseware with an unanswered survey, redirects to the survey
        """
        self._assert_survey_redirect(self.course)

    def test_anonymous_user_visiting_course_with_survey(self):
        """
        Verifies that anonymous user going to the courseware info with an unanswered survey is not
        redirected to survery and info page renders without server error.
        """
        self.logout()
        resp = self.client.get(
            reverse(
                'info',
                kwargs={'course_id': unicode(self.course.id)}
            )
        )
        self.assertEquals(resp.status_code, 200)

    def test_visiting_course_with_existing_answers(self):
        """
        Verifies that going to the courseware with an answered survey, there is no redirect
        """
        resp = self.client.post(
            self.postback_url,
            self.student_answers
        )
        self.assertEquals(resp.status_code, 200)

        self._assert_no_redirect(self.course)

    def test_course_id_field(self):
        """
        Assert that the course_id will be in the form fields, if available
        """

        resp = self.client.get(
            reverse(
                'course_survey',
                kwargs={'course_id': unicode(self.course.id)}
            )
        )

        self.assertEqual(resp.status_code, 200)
        expected = '<input type="hidden" name="course_id" value="{course_id}" />'.format(
            course_id=unicode(self.course.id)
        )

        self.assertContains(resp, expected)

    def test_course_id_persists(self):
        """
        Assert that a posted back course_id is stored in the database
        """

        answers = deepcopy(self.student_answers)
        answers.update({
            'course_id': unicode(self.course.id)
        })

        resp = self.client.post(
            self.postback_url,
            answers
        )
        self.assertEquals(resp.status_code, 200)

        self._assert_no_redirect(self.course)

        # however we want to make sure we persist the course_id
        answer_objs = SurveyAnswer.objects.filter(
            user=self.user,
            form=self.survey
        )

        for answer_obj in answer_objs:
            self.assertEquals(answer_obj.course_key, self.course.id)

    def test_visiting_course_with_bogus_survey(self):
        """
        Verifies that going to the courseware with a required, but non-existing survey, does not redirect
        """
        self._assert_no_redirect(self.course_with_bogus_survey)

    def test_visiting_survey_with_bogus_survey_name(self):
        """
        Verifies that going to the courseware with a required, but non-existing survey, does not redirect
        """

        resp = self.client.get(
            reverse(
                'course_survey',
                kwargs={'course_id': unicode(self.course_with_bogus_survey.id)}
            )
        )
        self.assertRedirects(
            resp,
            reverse('info', kwargs={'course_id': unicode(self.course_with_bogus_survey.id)})
        )

    def test_visiting_survey_with_no_course_survey(self):
        """
        Verifies that going to the courseware with a required, but non-existing survey, does not redirect
        """

        resp = self.client.get(
            reverse(
                'course_survey',
                kwargs={'course_id': unicode(self.course_without_survey.id)}
            )
        )
        self.assertRedirects(
            resp,
            reverse('info', kwargs={'course_id': unicode(self.course_without_survey.id)})
        )

    def test_survey_xss(self):
        """Test that course display names are correctly HTML-escaped."""
        response = self.client.get(
            reverse(
                'course_survey',
                kwargs={'course_id': unicode(self.course.id)}
            )
        )
        self.assert_xss(response, '<script>alert("XSS")</script>')
