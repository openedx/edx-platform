"""
Tests related to tasks.py file of the mailchimp pipeline app
"""
import json

import factory
import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.test import override_settings
from mock import ANY, patch

from common.djangoapps.mailchimp_pipeline.tests.helpers import create_organization, generate_mailchimp_url
from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.onboarding.models import FocusArea, OrgSector
from lms.djangoapps.onboarding.tests.factories import UserFactory
from mailchimp_pipeline.client import Connection, MailChimpException
from mailchimp_pipeline.helpers import (
    get_enrollements_course_short_ids,
    get_user_active_enrollements
)
from mailchimp_pipeline.signals.handlers import task_send_account_activation_email
from mailchimp_pipeline.tasks import update_enrollments_completions_at_mailchimp
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class MailchimpPipelineTaskTestClass(ModuleStoreTestCase):
    """
        Tests for tasks and generic functions
    """

    CREATE_USER = False

    @patch("nodebb.signals.handlers.get_current_request")
    @patch("common.lib.mandrill_client.client.MandrillClient.send_mail")
    def setUp(self, mocked_nodebb_request, mocked_email_sender):  # pylint: disable=unused-argument, arguments-differ
        super(MailchimpPipelineTaskTestClass, self).setUp()
        self.mailchimp_list_id = settings.MAILCHIMP_LEARNERS_LIST_ID
        patcher = patch('mailchimp_pipeline.client.request', autospec=True)
        self.mock_request = patcher.start()
        self.mock_request.return_value.status_code = 204
        self.addCleanup(patcher.stop)
        self.connection = Connection.get_connection()
        self.mail_chimp_root_url = self.connection.root
        self.user = UserFactory(is_staff=False, password='test')

        organization = create_organization(self.user)
        self.user.extended_profile.organization = organization
        self.user.extended_profile.save()
        course = CourseFactory.create(org="test", course="course", display_name="run")
        course.save()
        CourseEnrollment.enroll(self.user, course.id)

        self.connection = Connection.get_connection()
        self.mail_chimp_root_url = self.connection.root

    @patch("common.lib.mandrill_client.client.MandrillClient.send_mail")
    def test_task_send_account_activation_email(self, mocked_send_email):
        """
            Test if the test_task_send_account_activation_email task is sending email to MailChimp
            server with right user email and other user related data.
            :param mocked_send_email: Mocked email sender to check if it is called with right parameters
        """
        data = {
            'first_name': 'test',
            'activation_link': 'http://localhost:8000/activate/',
            'user_email': self.user.email
        }
        result = task_send_account_activation_email.delay(data)
        assert result.successful()
        expected_context = {
            'first_name': data['first_name'],
            'activation_link': data['activation_link'],
        }
        mocked_send_email.assert_called_with(ANY, self.user.email, expected_context)

    @factory.django.mute_signals(post_save)
    @patch("mailchimp_pipeline.tasks.connection")
    def test_update_enrollments_completions_at_mailchimp(self, mocked_connection):  # pylint: disable=unused-argument
        """
            Test if the update_enrollments_completions_at_mailchimp task is sending complete
            information of a user to the expected MailChimp URL
            :param mocked_connection: Mocked database connection to handle cursor

        """
        profile = self.user.profile
        profile.language = 'test_language'
        profile.city = 'test_city'
        profile.save()
        extended_profile = self.user.extended_profile

        all_certs = certificate_api.get_certificates_for_user(self.user.username)
        completed_course_keys = [
            cert.get('course_key', '') for cert in all_certs if certificate_api.is_passing_status(cert['status'])]
        completed_courses = CourseOverview.objects.filter(id__in=completed_course_keys)
        org_type = OrgSector.objects.get_map().get(extended_profile.organization.org_type, '')
        all_certs = certificate_api.get_certificates_for_user(self.user.username)

        result = update_enrollments_completions_at_mailchimp.delay(self.mailchimp_list_id)
        assert result.successful()

        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "FULLNAME": self.user.get_full_name(),
                "USERNAME": self.user.username,
                "LANG": profile.language,
                "COUNTRY": "",
                "CITY": profile.city,
                "DATEREGIS": str(self.user.date_joined.strftime("%m/%d/%Y")),
                "LSOURCE": "",
                "ENROLLS": get_user_active_enrollements(self.user.username),
                "ENROLL_IDS": get_enrollements_course_short_ids(self.user.username),
                "COMPLETES": ", ".join([course.display_name for course in completed_courses]),
                "ORG": extended_profile.organization.label,
                "ORGTYPE": org_type,
                "WORKAREA": str(FocusArea.get_map().get(extended_profile.organization.focus_area, ""))
            }
        }
        self.mock_request.assert_any_call(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    @patch("mailchimp_pipeline.tasks.connection")
    def test_update_enrollments_completions_at_mailchimp_for_mailchimp_exception(
            self, mocked_connection):  # pylint: disable=unused-argument
        """
            Test if the update_enrollments_completions_at_mailchimp task is raising an exception
            on response (from MailChimp server) status code  of 404
            :param mocked_connection: Mocked database connection to handle cursor
        """
        self.mock_request.return_value.status_code = 404
        self.mock_request.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
        update_enrollments_completions_at_mailchimp.delay(self.mailchimp_list_id)
        self.assertRaises(MailChimpException)

    @patch("lms.djangoapps.certificates.api.get_certificates_for_user")
    @patch("mailchimp_pipeline.tasks.connection")
    def test_update_enrollments_completions_at_mailchimp_for_certificate_exception(
            self, mocked_connection, mocked_certificate_api):  # pylint: disable=unused-argument
        """
            Test if the update_enrollments_completions_at_mailchimp task is raising an exception
            on failure of certificate API
            :param mocked_connection: Mocked database connection to handle cursor
            :param mocked_certificate_api: Mocked api function to produce exception
        """
        mocked_certificate_api.side_effect = Exception
        update_enrollments_completions_at_mailchimp.delay(self.mailchimp_list_id)
        self.assertRaises(Exception)

    @patch("mailchimp_pipeline.tasks.connection")
    def test_update_enrollments_completions_at_mailchimp_for_exception(
            self, mocked_connection):  # pylint: disable=unused-argument
        """
           Test if the update_enrollments_completions_at_mailchimp task is raising an exception
           when there is no extended-profile of the use
           :param mocked_connection: Mocked database connection to handle cursor
        """
        self.user.extended_profile.delete()
        update_enrollments_completions_at_mailchimp.delay(self.mailchimp_list_id)
        self.assertRaises(Exception)
