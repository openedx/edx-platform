"""
Unit tests for bulk-email-related models.
"""


import datetime

import ddt
from django.core.management import call_command
from django.test import TestCase
from mock import Mock, patch
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from lms.djangoapps.bulk_email.api import is_bulk_email_feature_enabled
from lms.djangoapps.bulk_email.models import (
    SEND_TO_COHORT,
    SEND_TO_STAFF,
    SEND_TO_TRACK,
    BulkEmailFlag,
    CourseAuthorization,
    CourseEmail,
    CourseEmailTemplate,
    Optout,
)
from common.djangoapps.course_modes.models import CourseMode
from openedx.core.djangoapps.course_groups.models import CourseCohort
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class CourseEmailTest(ModuleStoreTestCase):
    """Test the CourseEmail model."""

    def test_creation(self):
        course_id = CourseKey.from_string('abc/123/doremi')
        sender = UserFactory.create()
        to_option = SEND_TO_STAFF
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        email = CourseEmail.create(course_id, sender, [to_option], subject, html_message)
        self.assertEqual(email.course_id, course_id)
        self.assertIn(SEND_TO_STAFF, [target.target_type for target in email.targets.all()])
        self.assertEqual(email.subject, subject)
        self.assertEqual(email.html_message, html_message)
        self.assertEqual(email.sender, sender)

    def test_creation_with_optional_attributes(self):
        course_id = CourseKey.from_string('abc/123/doremi')
        sender = UserFactory.create()
        to_option = SEND_TO_STAFF
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        template_name = "branded_template"
        from_addr = "branded@branding.com"
        email = CourseEmail.create(
            course_id, sender, [to_option], subject, html_message, template_name=template_name, from_addr=from_addr
        )
        self.assertEqual(email.course_id, course_id)
        self.assertEqual(email.targets.all()[0].target_type, SEND_TO_STAFF)
        self.assertEqual(email.subject, subject)
        self.assertEqual(email.html_message, html_message)
        self.assertEqual(email.sender, sender)
        self.assertEqual(email.template_name, template_name)
        self.assertEqual(email.from_addr, from_addr)

    def test_bad_to_option(self):
        course_id = CourseKey.from_string('abc/123/doremi')
        sender = UserFactory.create()
        to_option = "fake"
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        with self.assertRaises(ValueError):
            CourseEmail.create(course_id, sender, to_option, subject, html_message)

    @ddt.data(
        datetime.datetime(1999, 1, 1, tzinfo=UTC),
        datetime.datetime(datetime.MAXYEAR, 1, 1, tzinfo=UTC),
    )
    def test_track_target(self, expiration_datetime):
        """
        Tests that emails can be sent to a specific track. Also checks that
         emails can be sent to an expired track (EDUCATOR-364)
        """
        course = CourseFactory.create()
        course_id = course.id
        sender = UserFactory.create()
        to_option = 'track:test'
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        CourseMode.objects.create(
            mode_slug='test',
            mode_display_name='Test',
            course_id=course_id,
            expiration_datetime=expiration_datetime,
        )
        email = CourseEmail.create(course_id, sender, [to_option], subject, html_message)
        self.assertEqual(len(email.targets.all()), 1)
        target = email.targets.all()[0]
        self.assertEqual(target.target_type, SEND_TO_TRACK)
        self.assertEqual(target.short_display(), 'track-test')
        self.assertEqual(target.long_display(), 'Course mode: Test, Currency: usd')

    @ddt.data(
        CourseMode.AUDIT,
        CourseMode.HONOR,
    )
    def test_track_target_with_free_mode(self, free_mode):
        """
        Tests that when emails are sent to a free track the track display
        should not contain currency.
        """
        course = CourseFactory.create()
        mode_display_name = free_mode.capitalize
        course_id = course.id
        sender = UserFactory.create()
        to_option = 'track:{}'.format(free_mode)
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        CourseMode.objects.create(
            mode_slug=free_mode,
            mode_display_name=mode_display_name,
            course_id=course_id,
        )

        email = CourseEmail.create(course_id, sender, [to_option], subject, html_message)
        self.assertEqual(len(email.targets.all()), 1)
        target = email.targets.all()[0]
        self.assertEqual(target.target_type, SEND_TO_TRACK)
        self.assertEqual(target.short_display(), 'track-{}'.format(free_mode))
        self.assertEqual(target.long_display(), u'Course mode: {}'.format(mode_display_name))

    def test_cohort_target(self):
        course_id = CourseKey.from_string('abc/123/doremi')
        sender = UserFactory.create()
        to_option = 'cohort:test cohort'
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        CourseCohort.create(cohort_name='test cohort', course_id=course_id)
        email = CourseEmail.create(course_id, sender, [to_option], subject, html_message)
        self.assertEqual(len(email.targets.all()), 1)
        target = email.targets.all()[0]
        self.assertEqual(target.target_type, SEND_TO_COHORT)
        self.assertEqual(target.short_display(), 'cohort-test cohort')
        self.assertEqual(target.long_display(), 'Cohort: test cohort')


class OptoutTest(TestCase):
    def test_is_user_opted_out_for_course(self):
        user = UserFactory.create()
        course_id = CourseKey.from_string('abc/123/doremi')

        self.assertFalse(Optout.is_user_opted_out_for_course(user, course_id))

        Optout.objects.create(
            user=user,
            course_id=course_id,
        )

        self.assertTrue(Optout.is_user_opted_out_for_course(user, course_id))


class NoCourseEmailTemplateTest(TestCase):
    """Test the CourseEmailTemplate model without loading the template data."""

    def test_get_missing_template(self):
        with self.assertRaises(CourseEmailTemplate.DoesNotExist):
            CourseEmailTemplate.get_template()


class CourseEmailTemplateTest(TestCase):
    """Test the CourseEmailTemplate model."""

    def setUp(self):
        super(CourseEmailTemplateTest, self).setUp()

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

    def _get_sample_plain_context(self):
        """Provide sample context sufficient for rendering plaintext template"""
        context = {
            'course_title': "Bogus Course Title",
            'course_url': "/location/of/course/url",
            'email_settings_url': "/location/of/email/settings/url",
            'platform_name': 'edX',
            'email': 'your-email@test.com',
            'unsubscribe_link': '/bulk_email/email/optout/dummy'
        }
        return context

    def _get_sample_html_context(self):
        """Provide sample context sufficient for rendering HTML template"""
        context = self._get_sample_plain_context()
        context['course_image_url'] = "/location/of/course/image/url"
        return context

    def _add_xss_fields(self, context):
        """ Add fields to the context for XSS testing. """
        context['course_title'] = "<script>alert('Course Title!');</alert>"
        context['name'] = "<script>alert('Profile Name!');</alert>"
        # Must have user_id and course_id present in order to do keyword substitution
        context['user_id'] = 12345
        context['course_id'] = "course-v1:edx+100+1"
        return context

    def test_get_template(self):
        # Get the default template, which has name=None
        template = CourseEmailTemplate.get_template()
        self.assertIsNotNone(template.html_template)
        self.assertIsNotNone(template.plain_template)

    def test_get_branded_template(self):
        # Get a branded (non default) template and make sure we get what we expect
        template = CourseEmailTemplate.get_template(name="branded.template")
        self.assertIsNotNone(template.html_template)
        self.assertIsNotNone(template.plain_template)
        self.assertIn(u"THIS IS A BRANDED HTML TEMPLATE", template.html_template)
        self.assertIn(u"THIS IS A BRANDED TEXT TEMPLATE", template.plain_template)

    def test_render_html_without_context(self):
        template = CourseEmailTemplate.get_template()
        base_context = self._get_sample_html_context()
        for keyname in base_context:
            context = dict(base_context)
            del context[keyname]
            with self.assertRaises(KeyError):
                template.render_htmltext("My new html text.", context)

    def test_render_plaintext_without_context(self):
        template = CourseEmailTemplate.get_template()
        base_context = self._get_sample_plain_context()
        for keyname in base_context:
            context = dict(base_context)
            del context[keyname]
            with self.assertRaises(KeyError):
                template.render_plaintext("My new plain text.", context)

    def test_render_html(self):
        template = CourseEmailTemplate.get_template()
        context = self._get_sample_html_context()
        template.render_htmltext("My new html text.", context)

    def test_render_html_xss(self):
        template = CourseEmailTemplate.get_template()
        context = self._add_xss_fields(self._get_sample_html_context())
        message = template.render_htmltext(
            u"Dear %%USER_FULLNAME%%, thanks for enrolling in %%COURSE_DISPLAY_NAME%%.", context
        )
        self.assertNotIn("<script>", message)
        self.assertIn("&lt;script&gt;alert(&#39;Course Title!&#39;);&lt;/alert&gt;", message)
        self.assertIn("&lt;script&gt;alert(&#39;Profile Name!&#39;);&lt;/alert&gt;", message)

    def test_render_plain(self):
        template = CourseEmailTemplate.get_template()
        context = self._get_sample_plain_context()
        template.render_plaintext("My new plain text.", context)

    def test_render_plain_no_escaping(self):
        template = CourseEmailTemplate.get_template()
        context = self._add_xss_fields(self._get_sample_plain_context())
        message = template.render_plaintext(
            u"Dear %%USER_FULLNAME%%, thanks for enrolling in %%COURSE_DISPLAY_NAME%%.", context
        )
        self.assertNotIn("&lt;script&gt;", message)
        self.assertIn(context['course_title'], message)
        self.assertIn(context['name'], message)


class CourseAuthorizationTest(TestCase):
    """Test the CourseAuthorization model."""

    def tearDown(self):
        super(CourseAuthorizationTest, self).tearDown()
        BulkEmailFlag.objects.all().delete()

    def test_creation_auth_on(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=True)
        course_id = CourseKey.from_string('abc/123/doremi')
        # Test that course is not authorized by default
        self.assertFalse(is_bulk_email_feature_enabled(course_id))

        # Authorize
        cauth = CourseAuthorization(course_id=course_id, email_enabled=True)
        cauth.save()
        # Now, course should be authorized
        self.assertTrue(is_bulk_email_feature_enabled(course_id))
        self.assertEqual(
            str(cauth),
            "Course 'abc/123/doremi': Instructor Email Enabled"
        )

        # Unauthorize by explicitly setting email_enabled to False
        cauth.email_enabled = False
        cauth.save()
        # Test that course is now unauthorized
        self.assertFalse(is_bulk_email_feature_enabled(course_id))
        self.assertEqual(
            str(cauth),
            "Course 'abc/123/doremi': Instructor Email Not Enabled"
        )

    def test_creation_auth_off(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)
        course_id = CourseKey.from_string('blahx/blah101/ehhhhhhh')
        # Test that course is authorized by default, since auth is turned off
        self.assertTrue(is_bulk_email_feature_enabled(course_id))

        # Use the admin interface to unauthorize the course
        cauth = CourseAuthorization(course_id=course_id, email_enabled=False)
        cauth.save()

        # Now, course should STILL be authorized!
        self.assertTrue(is_bulk_email_feature_enabled(course_id))
