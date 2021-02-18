import json
import requests
import factory
from mock import ANY, patch
from datetime import datetime
from django.conf import settings
from django.test import override_settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from common.djangoapps.mailchimp_pipeline.tests.helpers import create_organization, generate_mailchimp_url
from lms.djangoapps.onboarding.tests.factories import UserFactory, UserExtendedProfileFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from lms.djangoapps.onboarding.models import OrganizationMetricUpdatePrompt
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from lms.djangoapps.onboarding.models import FocusArea, OrgSector
from lms.djangoapps.certificates import api as certificate_api
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserProfileFactory
from student.models import CourseEnrollment

from mailchimp_pipeline.tasks import update_org_details_at_mailchimp, update_enrollments_completions_at_mailchimp
from mailchimp_pipeline.helpers import (
    get_enrollements_course_short_ids,
    get_org_data_for_mandrill,
    get_user_active_enrollements
)
from mailchimp_pipeline.client import MailChimpException, Connection
from mailchimp_pipeline.signals.handlers import (
    send_user_info_to_mailchimp,
    sync_metric_update_prompt_with_mail_chimp,
    update_mailchimp,
    send_user_enrollments_to_mailchimp,
    task_send_account_activation_email,
    task_send_user_info_to_mailchimp,
    send_user_course_completions_to_mailchimp
)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class MailchimpPipelineTaskTestClass(ModuleStoreTestCase):
    """
        Tests for tasks and generic functions
    """

    CREATE_USER = False

    @patch("nodebb.signals.handlers.get_current_request")
    @patch("common.lib.mandrill_client.client.MandrillClient.send_mail")
    def setUp(self, mocked_nodebb_request, mocked_email_sender):
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

    def test_update_mailchimp(self):
        """
            Test if the update_mailchimp function is sending `PUT` request on exact MailChimp URL
            with expected data
        """
        data = {'data': 'test_data'}
        update_mailchimp(self.user.email, data)
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(data), auth=ANY, params=ANY)

    def test_update_mailchimp_for_exception(self):
        """
            Test if update_mailchimp function generates MailChimp exception on getting response
            (from MailChimp server request) status code of 404
        """
        self.mock_request.return_value.status_code = 404
        self.mock_request.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError
        update_mailchimp(self.user.email, {})
        self.assertRaises(MailChimpException)

    def test_task_send_user_course_completions_to_mailchimp(self):
        """
            Test if the send_user_course_completions_to_mailchimp task is sending completed course
            information perfectly to the MailChimp expected URL
        """
        data = {'user_id': self.user.id, 'created': True}
        result = send_user_course_completions_to_mailchimp.delay(data)
        assert result.successful()
        all_certs = certificate_api.get_certificates_for_user(self.user.username)
        completed_course_keys = [
            cert.get('course_key', '') for cert in all_certs if certificate_api.is_passing_status(cert['status'])]
        completed_courses = CourseOverview.objects.filter(id__in=completed_course_keys)
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "COMPLETES": ", ".join([course.display_name for course in completed_courses]),
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    @patch("lms.djangoapps.certificates.api.get_certificates_for_user")
    def test_task_send_user_course_completions_to_mailchimp_for_exception(self, mocked_certificates_api):
        """
            Test if the send_user_course_completions_to_mailchimp task is raising an exception on
            certificates API failure
            :mocked_certificates_api: Mocked certificate api function to produce exception
        """
        mocked_certificates_api.side_effect = Exception
        data = {'user_id': self.user.id, 'created': True}
        send_user_course_completions_to_mailchimp.delay(data)
        self.assertRaises(Exception)

    def test_send_user_info_to_mailchimp(self):
        """
            Test if the send_user_info_to_mailchimp function is sending user information perfectly
            to the MailChimp expected URL
        """
        send_user_info_to_mailchimp('test', self.user, True, kwargs={})
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "FULLNAME": self.user.get_full_name(),
                "USERNAME": self.user.username,
                "DATEREGIS": str(self.user.date_joined.strftime("%m/%d/%Y"))
            },
            "email_address": self.user.email,
            "status_if_new": "subscribed"
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    def test_sync_metric_update_prompt_with_mail_chimp(self):
        """
            Test if the sync_metric_update_prompt_with_mail_chimp function is sending Organization
            Metric Update Prompt data perfectly to the MailChimp expected URL
        """
        organization = self.user.extended_profile.organization
        update_prompt = OrganizationMetricUpdatePrompt(
            org=organization,
            responsible_user=self.user,
            year=True,
            year_month=True,
            latest_metric_submission=datetime.now()
        )
        sync_metric_update_prompt_with_mail_chimp(update_prompt)
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "YEAR": 'TRUE',
                "Y_MONTH": 'TRUE',
                "Y_3MONTHS": 'FALSE',
                "Y_6MONTHS": 'FALSE'
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

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

    def test_task_send_user_info_to_mailchimp(self):
        """
            Test if the task_send_user_info_to_mailchimp task is sending user information
            perfectly to the MailChimp expected URL
        """
        data = {
            'user_id': self.user.id,
            'created': True
        }
        result = task_send_user_info_to_mailchimp.delay(data)
        assert result.successful()
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "FULLNAME": self.user.get_full_name(),
                "USERNAME": self.user.username,
                "DATEREGIS": str(self.user.date_joined.strftime("%m/%d/%Y"))
            },
            "email_address": self.user.email,
            "status_if_new": "subscribed"
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    @factory.django.mute_signals(post_save)
    def test_send_user_enrollments_to_mailchimp(self):
        """
            Test if the send_user_enrollments_to_mailchimp function is sending user enrolled courses
            information perfectly to the MailChimp expected URL
        """
        send_user_enrollments_to_mailchimp(self.user)
        enrollment_titles = get_user_active_enrollements(self.user.username)
        enrollment_short_ids = get_enrollements_course_short_ids(self.user.username)
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "ENROLLS": enrollment_titles,
                "ENROLL_IDS": enrollment_short_ids
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    def test_task_update_org_details_at_mailchimp(self):
        """
            Test if the update_org_details_at_mailchimp task is sending organization information
            perfectly to the MailChimp expected URL
        """
        organization = create_organization(self.user)
        org_label, org_type, work_area = get_org_data_for_mandrill(organization)
        result = update_org_details_at_mailchimp.delay(
            org_label, org_type, work_area, organization.id, self.mailchimp_list_id
        )
        assert result.successful()
        expected_url = generate_mailchimp_url(self.mail_chimp_root_url, self.user.email)
        expected_data = {
            "merge_fields": {
                "ORG": org_label,
                "ORGTYPE": org_type,
                "WORKAREA": work_area
            }
        }
        self.mock_request.assert_called_with(
            "PUT", url=expected_url, headers=ANY, data=json.dumps(expected_data), auth=ANY, params=ANY)

    def test_task_update_org_details_at_mailchimp_for_exception(self):
        """
            Test if the update_org_details_at_mailchimp task is raising a MailChimp exception on
            response (from MailChimp server) status code  of 404
        """
        self.mock_request.return_value.status_code = 404
        self.mock_request.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError

        organization = create_organization(self.user)
        org_label, org_type, work_area = get_org_data_for_mandrill(organization)
        update_org_details_at_mailchimp.delay(
            org_label, org_type, work_area, organization.id, self.mailchimp_list_id
        )

        self.assertRaises(MailChimpException)

    @factory.django.mute_signals(post_save)
    @patch("mailchimp_pipeline.tasks.connection")
    def test_update_enrollments_completions_at_mailchimp(self, mocked_connection):
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
    def test_update_enrollments_completions_at_mailchimp_for_mailchimp_exception(self, mocked_connection):
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
    def test_update_enrollments_completions_at_mailchimp_for_certificate_exception(self,
                                                                                   mocked_connection,
                                                                                   mocked_certificate_api):
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
    def test_update_enrollments_completions_at_mailchimp_for_exception(self, mocked_connection):
        """
           Test if the update_enrollments_completions_at_mailchimp task is raising an exception
           when there is no extended-profile of the use
           :param mocked_connection: Mocked database connection to handle cursor
        """
        self.user.extended_profile.delete()
        update_enrollments_completions_at_mailchimp.delay(self.mailchimp_list_id)
        self.assertRaises(Exception)
