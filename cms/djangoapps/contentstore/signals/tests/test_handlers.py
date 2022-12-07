"""
Tests for signal handlers in the contentstore.
"""

import attr
import httpretty
from datetime import datetime, timezone
import json
import requests
from unittest.mock import patch
from django.test import TestCase
from django.test.utils import override_settings
from opaque_keys.edx.locator import CourseLocator, LibraryLocator
from openedx_events.content_authoring.data import (
    CertificateSignatoryData,
    CertificateConfigData,
    CourseCatalogData,
    CourseScheduleData,
)
from openedx_events.content_authoring.signals import (
    COURSE_CERTIFICATE_CONFIG_DELETED,
    COURSE_CERTIFICATE_CONFIG_CHANGED,
)
import cms.djangoapps.contentstore.signals.handlers as sh
from xmodule.modulestore.edit_info import EditInfoMixin
from cms.djangoapps.contentstore.tests.utils import CERTIFICATE_JSON_WITH_SIGNATORIES
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.django import SignalHandler
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import SampleCourseFactory


class TestCatalogInfoSignal(ModuleStoreTestCase):
    """
    Test functionality of triggering catalog info signals (and events) from course_published signal.
    """

    def setUp(self):
        super().setUp()
        self.course = SampleCourseFactory.create(
            org='TestU',
            number='sig101',
            display_name='Signals 101',
            run='Summer2022',
        )
        self.course_key = self.course.id

        self.expected_data = CourseCatalogData(
            course_key=CourseLocator(org='TestU', course='sig101', run='Summer2022', branch=None, version_guid=None),
            name='Signals 101',
            schedule_data=CourseScheduleData(
                start=datetime.fromisoformat('2030-01-01T00:00+00:00'),
                pacing='instructor',
                end=None,
                enrollment_start=None,
                enrollment_end=None),
            hidden=False,
            invitation_only=False
        )

    @patch(
        'cms.djangoapps.contentstore.signals.handlers.transaction.on_commit',
        autospec=True, side_effect=lambda func: func(),  # run right away
    )
    @patch('cms.djangoapps.contentstore.signals.handlers.emit_catalog_info_changed_signal', autospec=True)
    def test_signal_chain(self, mock_emit, _mock_on_commit):
        """
        Test that the course_published signal handler invokes the catalog info signal emitter.

        I tested this in a bit of a weird way because I couldn't get the transaction on-commit
        to run during the test, so instead I capture it and call the callbacks right away.
        """
        with SignalHandler.course_published.for_state(is_enabled=True):
            SignalHandler.course_published.send(TestCatalogInfoSignal, course_key=self.course_key)
        mock_emit.assert_called_once_with(self.course_key)

    @override_settings(SEND_CATALOG_INFO_SIGNAL=True)
    @patch('cms.djangoapps.contentstore.signals.handlers.COURSE_CATALOG_INFO_CHANGED', autospec=True)
    def test_emit_regular_course(self, mock_signal):
        """On a normal course publish, send an event."""
        now = datetime.now()
        with patch.object(EditInfoMixin, 'subtree_edited_on', now):
            sh.emit_catalog_info_changed_signal(self.course_key)
        mock_signal.send_event.assert_called_once_with(
            time=now.replace(tzinfo=timezone.utc),
            catalog_info=self.expected_data)

    @override_settings(SEND_CATALOG_INFO_SIGNAL=True)
    @patch('cms.djangoapps.contentstore.signals.handlers.COURSE_CATALOG_INFO_CHANGED', autospec=True)
    def test_ignore_library(self, mock_signal):
        """When course key is actually a library, don't send."""
        sh.emit_catalog_info_changed_signal(LibraryLocator(org='SomeOrg', library='stuff'))
        mock_signal.send_event.assert_not_called()

    @override_settings(SEND_CATALOG_INFO_SIGNAL=False)
    @patch('cms.djangoapps.contentstore.signals.handlers.COURSE_CATALOG_INFO_CHANGED', autospec=True)
    def test_disabled(self, mock_signal):
        """When toggle is disabled, don't send."""
        sh.emit_catalog_info_changed_signal(self.course_key)
        mock_signal.send_event.assert_not_called()


class TestCourseCertificateConfigSignal(ModuleStoreTestCase):
    """
    Test functionality of triggering course certificate config signals (and events).
    """

    def setUp(self):
        super().setUp()
        signatory = CERTIFICATE_JSON_WITH_SIGNATORIES['signatories'][0]
        self.course = SampleCourseFactory.create(
            org='TestU',
            number='sig101',
            display_name='Signals 101',
            run='Summer2022',
        )
        self.course_key = self.course.id
        self.expected_data = CertificateConfigData(
            course_id=str(self.course_key),
            title=CERTIFICATE_JSON_WITH_SIGNATORIES['name'],
            is_active=CERTIFICATE_JSON_WITH_SIGNATORIES['is_active'],
            certificate_type='verified',
            signatories=[
                CertificateSignatoryData(
                    name=signatory['name'],
                    title=signatory['title'],
                    organization=signatory['organization'],
                    image=signatory['signature_image_path']
                )
            ],
        )

    @patch('cms.djangoapps.contentstore.signals.handlers.COURSE_CERTIFICATE_CONFIG_CHANGED.send_event', autospec=True)
    def test_course_certificate_config_changed(self, mock_signal):
        """
        Test that the change event is fired when course is in state where a certificate is available.
        """
        CourseModeFactory.create(mode_slug='verified', course_id=self.course.id)
        sh.emit_course_certificate_config_changed_signal(str(self.course_key), CERTIFICATE_JSON_WITH_SIGNATORIES)
        mock_signal.assert_called_once_with(certificate_config=self.expected_data)

    @patch('cms.djangoapps.contentstore.signals.handlers.COURSE_CERTIFICATE_CONFIG_CHANGED.send_event', autospec=True)
    def test_course_certificate_config_changed_does_not_emit(self, mock_signal):
        """
        Test that the change event is not fired when course is in state where a certificate is not available.
        """
        CourseModeFactory.create(mode_slug='audit', course_id=self.course.id)
        sh.emit_course_certificate_config_changed_signal(str(self.course_key), CERTIFICATE_JSON_WITH_SIGNATORIES)
        mock_signal.assert_not_called()

    @patch('cms.djangoapps.contentstore.signals.handlers.COURSE_CERTIFICATE_CONFIG_DELETED.send_event', autospec=True)
    def test_course_certificate_config_deleted(self, mock_signal):
        """
        Test that the delete event is fired when course is in state where a certificate is available.
        """
        CourseModeFactory.create(mode_slug='verified', course_id=self.course.id)
        sh.emit_course_certificate_config_deleted_signal(str(self.course_key), CERTIFICATE_JSON_WITH_SIGNATORIES)
        mock_signal.assert_called_once_with(certificate_config=self.expected_data)

    @patch('cms.djangoapps.contentstore.signals.handlers.COURSE_CERTIFICATE_CONFIG_DELETED.send_event', autospec=True)
    def test_course_certificate_config_deleted_does_not_emit(self, mock_signal):
        """
        Test that the delete event is not fired when course is in state where a certificate is not available.
        """
        CourseModeFactory.create(mode_slug='audit', course_id=self.course.id)
        sh.emit_course_certificate_config_deleted_signal(str(self.course_key), CERTIFICATE_JSON_WITH_SIGNATORIES)
        mock_signal.assert_not_called()


class SignalCourseCertificateConfigurationListenerTestCase(TestCase):
    """
    Test case for end listeners of signals:
        - COURSE_CERTIFICATE_CONFIG_DELETED,
        - COURSE_CERTIFICATE_CONFIG_CHANGED.
    """

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username='cred-user')
        self.course_key = CourseLocator(org='TestU', course='sig101', run='Summer2022', branch=None, version_guid=None)
        self.expected_data = CertificateConfigData(
            course_id=str(self.course_key),
            title=CERTIFICATE_JSON_WITH_SIGNATORIES['name'],
            is_active=CERTIFICATE_JSON_WITH_SIGNATORIES['is_active'],
            certificate_type='verified',
            signatories=[
                CertificateSignatoryData(
                    name=CERTIFICATE_JSON_WITH_SIGNATORIES['signatories'][0]['name'],
                    title=CERTIFICATE_JSON_WITH_SIGNATORIES['signatories'][0]['title'],
                    organization=CERTIFICATE_JSON_WITH_SIGNATORIES['signatories'][0]['organization'],
                    image=CERTIFICATE_JSON_WITH_SIGNATORIES['signatories'][0]['signature_image_path']
                )
            ],
        )

    @patch('cms.djangoapps.contentstore.signals.handlers.delete_course_certificate_configuration')
    def test_course_certificate_config_deleted_listener(self, mock_delete_course_certificate_configuration):
        """
        Ensure the correct API call when the signal COURSE_CERTIFICATE_CONFIG_DELETED happened.
        """
        COURSE_CERTIFICATE_CONFIG_DELETED.send_event(certificate_config=self.expected_data)

        mock_delete_course_certificate_configuration.assert_called_once()
        call = mock_delete_course_certificate_configuration.mock_calls[0]
        __, (given_course_key, given_config), __ = call
        assert given_course_key == str(self.course_key)
        assert given_config == attr.asdict(self.expected_data)

    @patch('cms.djangoapps.contentstore.signals.handlers.send_course_certificate_configuration')
    def test_course_certificate_config_changed_listener(self, mock_send_course_certificate_configuration):
        """
        Ensure the correct API call when the signal COURSE_CERTIFICATE_CONFIG_CHANGED happened.
        """
        COURSE_CERTIFICATE_CONFIG_CHANGED.send_event(certificate_config=self.expected_data)

        mock_send_course_certificate_configuration.assert_called_once()
        call = mock_send_course_certificate_configuration.mock_calls[0]
        __, (given_course_key, given_config, __), __ = call
        assert given_course_key == str(self.course_key)
        assert given_config == attr.asdict(self.expected_data)
