"""
Unit tests for bulk-email-related models.
"""
from django.test import TestCase
from django.core.management import call_command
from django.conf import settings

from student.tests.factories import UserFactory

from mock import patch, Mock
from nose.plugins.attrib import attr

from bulk_email.models import CourseEmail, SEND_TO_STAFF, CourseEmailTemplate, CourseAuthorization
from opaque_keys.edx.locations import SlashSeparatedCourseKey


@attr('shard_1')
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message'))
class CourseEmailTest(TestCase):
    """Test the CourseEmail model."""

    def test_creation(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        sender = UserFactory.create()
        to_option = SEND_TO_STAFF
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        email = CourseEmail.create(course_id, sender, to_option, subject, html_message)
        self.assertEquals(email.course_id, course_id)
        self.assertEquals(email.to_option, SEND_TO_STAFF)
        self.assertEquals(email.subject, subject)
        self.assertEquals(email.html_message, html_message)
        self.assertEquals(email.sender, sender)

    def test_creation_with_optional_attributes(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        sender = UserFactory.create()
        to_option = SEND_TO_STAFF
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        template_name = "branded_template"
        from_addr = "branded@branding.com"
        email = CourseEmail.create(course_id, sender, to_option, subject, html_message, template_name=template_name, from_addr=from_addr)
        self.assertEquals(email.course_id, course_id)
        self.assertEquals(email.to_option, SEND_TO_STAFF)
        self.assertEquals(email.subject, subject)
        self.assertEquals(email.html_message, html_message)
        self.assertEquals(email.sender, sender)
        self.assertEquals(email.template_name, template_name)
        self.assertEquals(email.from_addr, from_addr)

    def test_bad_to_option(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        sender = UserFactory.create()
        to_option = "fake"
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        with self.assertRaises(ValueError):
            CourseEmail.create(course_id, sender, to_option, subject, html_message)


@attr('shard_1')
class NoCourseEmailTemplateTest(TestCase):
    """Test the CourseEmailTemplate model without loading the template data."""

    def test_get_missing_template(self):
        with self.assertRaises(CourseEmailTemplate.DoesNotExist):
            CourseEmailTemplate.get_template()


@attr('shard_1')
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
            'account_settings_url': "/location/of/account/settings/url",
            'platform_name': 'edX',
            'email': 'your-email@test.com',
        }
        return context

    def _get_sample_html_context(self):
        """Provide sample context sufficient for rendering HTML template"""
        context = self._get_sample_plain_context()
        context['course_image_url'] = "/location/of/course/image/url"
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

    def test_render_plain(self):
        template = CourseEmailTemplate.get_template()
        context = self._get_sample_plain_context()
        template.render_plaintext("My new plain text.", context)


@attr('shard_1')
class CourseAuthorizationTest(TestCase):
    """Test the CourseAuthorization model."""

    @patch.dict(settings.FEATURES, {'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_creation_auth_on(self):
        course_id = SlashSeparatedCourseKey('abc', '123', 'doremi')
        # Test that course is not authorized by default
        self.assertFalse(CourseAuthorization.instructor_email_enabled(course_id))

        # Authorize
        cauth = CourseAuthorization(course_id=course_id, email_enabled=True)
        cauth.save()
        # Now, course should be authorized
        self.assertTrue(CourseAuthorization.instructor_email_enabled(course_id))
        self.assertEquals(
            cauth.__unicode__(),
            "Course 'abc/123/doremi': Instructor Email Enabled"
        )

        # Unauthorize by explicitly setting email_enabled to False
        cauth.email_enabled = False
        cauth.save()
        # Test that course is now unauthorized
        self.assertFalse(CourseAuthorization.instructor_email_enabled(course_id))
        self.assertEquals(
            cauth.__unicode__(),
            "Course 'abc/123/doremi': Instructor Email Not Enabled"
        )

    @patch.dict(settings.FEATURES, {'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_creation_auth_off(self):
        course_id = SlashSeparatedCourseKey('blahx', 'blah101', 'ehhhhhhh')
        # Test that course is authorized by default, since auth is turned off
        self.assertTrue(CourseAuthorization.instructor_email_enabled(course_id))

        # Use the admin interface to unauthorize the course
        cauth = CourseAuthorization(course_id=course_id, email_enabled=False)
        cauth.save()

        # Now, course should STILL be authorized!
        self.assertTrue(CourseAuthorization.instructor_email_enabled(course_id))
