"""
Tests for renderer.py
"""

import json
from django.test import TestCase
import pytz
import datetime


from edx_notifications.const import (
    RENDER_FORMAT_HTML,
    RENDER_FORMAT_SMS,
    RENDER_FORMAT_JSON
)
from edx_notifications.renderers.renderer import (
    BaseNotificationRenderer,
    get_renderer_for_type,
)

from edx_notifications.renderers.basic import (
    UnderscoreStaticFileRenderer,
    JsonRenderer
)

from edx_notifications.data import NotificationMessage, NotificationType
from edx_notifications.lib.publisher import register_notification_type


class TestBadRenderer(BaseNotificationRenderer):
    """
    For test purposes derive from BaseNotificationRenderer but only
    access base implementation
    """

    def can_render_format(self, render_format):
        """
        Returns (True/False) whether this renderer provides renderings
        into the requested format.
        """
        super(TestBadRenderer, self).can_render_format(render_format)

    def render(self, msg, render_format, lang):
        """
        This basic renderer just returns the subject in the Msg payload
        """
        super(TestBadRenderer, self).render(msg, render_format, lang)

    def get_template_path(self, render_format):
        """
        Return a path to where a client can get the template
        """
        super(TestBadRenderer, self).get_template_path(render_format)


class TestUnderscoreStaticFileRenderer(UnderscoreStaticFileRenderer):
    """
    Simulates the use of an Underscore renderer
    """
    underscore_template_name = 'edx_notifications.renderers.basic.BasicSubjectBodyRenderer'


class RendererTests(TestCase):
    """
    Test cases for renderer.py
    """

    def test_no_base_instatiation(self):
        """
        Asserts that we cannot create an instance of the abstract
        base class
        """

        with self.assertRaises(TypeError):
            BaseNotificationRenderer()  # pylint: disable=abstract-class-instantiated

    def test_cant_access_base_classes(self):
        """
        Try to access a test derived class from BaseNotificationRenderer
        that only delegates to the base class
        """

        bad = TestBadRenderer()

        with self.assertRaises(NotImplementedError):
            bad.can_render_format(None)

        with self.assertRaises(NotImplementedError):
            bad.render(None, None, None)

        with self.assertRaises(NotImplementedError):
            bad.get_template_path(None)

    def test_underscore(self):
        """
        Tests on the UnderscoreStaticFileRenderer
        """

        renderer = TestUnderscoreStaticFileRenderer('basic_subject_body.underscore')

        self.assertTrue(renderer.can_render_format(RENDER_FORMAT_HTML))

        msg_type = NotificationType(
            name='open-edx.edx_notifications.lib.tests.test_publisher',
            renderer='edx_notifications.renderers.basic.BasicSubjectBodyRenderer',
        )
        register_notification_type(msg_type)

        self.assertIsNotNone(get_renderer_for_type(msg_type))
        msg = NotificationMessage(
            namespace='test-runner',
            msg_type=msg_type,
            payload={
                'subject': 'test subject',
                'body': 'test body',
            },
            created=datetime.datetime.now(pytz.UTC)
        )

        renderer.get_template_path(RENDER_FORMAT_HTML)

        with self.assertRaises(NotImplementedError):
            renderer.get_template_path(RENDER_FORMAT_SMS)

        with self.assertRaises(NotImplementedError):
            renderer.render(msg, RENDER_FORMAT_SMS, None)

        html = renderer.render(msg, RENDER_FORMAT_HTML, None)

        with self.assertRaises(NotImplementedError):
            renderer.get_template_path(RENDER_FORMAT_SMS)

        self.assertIn('test subject', html)
        self.assertIn('test body', html)
        self.assertIn("<div class='xns-title'>", html)
        self.assertIn("<div class='xns-body'>", html)

        with self.assertRaises(Exception):
            bad_renderer = TestUnderscoreStaticFileRenderer('foo.underscore')
            bad_renderer.render(msg, RENDER_FORMAT_HTML, None)

    def test_json_renderer(self):
        """
        Make sure JSON renderer returns correct renderings
        """

        msg_type = NotificationType(
            name='open-edx.edx_notifications.lib.tests.test_publisher',
            renderer='edx_notifications.renderers.basic.JsonRenderer',
        )
        register_notification_type(msg_type)

        msg = NotificationMessage(
            namespace='test-runner',
            msg_type=msg_type,
            payload={
                'subject': 'test subject',
                'body': 'test body',
            }
        )

        renderer = JsonRenderer()

        self.assertTrue(renderer.can_render_format(RENDER_FORMAT_JSON))
        self.assertIsNone(renderer.get_template_path(RENDER_FORMAT_JSON))
        self.assertEqual(json.loads(renderer.render(msg, RENDER_FORMAT_JSON, None)), msg.payload)
