"""
Unit tests for bulk-email-related models.
"""
from django.test import TestCase
from django.core.management import call_command

from student.tests.factories import UserFactory

from bulk_email.models import CourseEmail, SEND_TO_STAFF, CourseEmailTemplate


class CourseEmailTest(TestCase):
    """Test the CourseEmail model."""

    def test_creation(self):
        course_id = 'abc/123/doremi'
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

    def test_bad_to_option(self):
        course_id = 'abc/123/doremi'
        sender = UserFactory.create()
        to_option = "fake"
        subject = "dummy subject"
        html_message = "<html>dummy message</html>"
        with self.assertRaises(ValueError):
            CourseEmail.create(course_id, sender, to_option, subject, html_message)


class NoCourseEmailTemplateTest(TestCase):
    """Test the CourseEmailTemplate model without loading the template data."""

    def test_get_missing_template(self):
        with self.assertRaises(CourseEmailTemplate.DoesNotExist):
            CourseEmailTemplate.get_template()


class CourseEmailTemplateTest(TestCase):
    """Test the CourseEmailTemplate model."""

    def setUp(self):
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
        template = CourseEmailTemplate.get_template()
        self.assertIsNotNone(template.html_template)
        self.assertIsNotNone(template.plain_template)

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
