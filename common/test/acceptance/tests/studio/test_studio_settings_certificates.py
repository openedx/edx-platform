"""
Acceptance tests for Studio's Setting pages
"""
import re
import uuid

from nose.plugins.attrib import attr

from .base_studio_test import StudioCourseTest
from ...pages.lms.create_mode import ModeCreationPage
from ...pages.studio.settings_certificates import CertificatesPage
from ...pages.studio.settings_advanced import AdvancedSettingsPage


@attr('shard_8')
class CertificatesTest(StudioCourseTest):
    """
    Tests for settings/certificates Page.
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(CertificatesTest, self).setUp(is_staff=True)
        self.certificates_page = CertificatesPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.advanced_settings_page = AdvancedSettingsPage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )
        self.course_advanced_settings = dict()

        # Add a verified mode to the course
        ModeCreationPage(
            self.browser, self.course_id, mode_slug=u'verified', mode_display_name=u'Verified Certificate',
            min_price=10, suggested_prices='10,20'
        ).visit()

    def make_signatory_data(self, prefix='First'):
        """
        Makes signatory dict which can be used in the tests to create certificates
        """
        return {
            'name': '{prefix} Signatory Name'.format(prefix=prefix),
            'title': '{prefix} Signatory Title'.format(prefix=prefix),
            'organization': '{prefix} Signatory Organization'.format(prefix=prefix),
        }

    def create_and_verify_certificate(self, course_title_override, existing_certs, signatories):
        """
        Creates a new certificate and verifies that it was properly created.
        """
        self.assertEqual(existing_certs, len(self.certificates_page.certificates))
        if existing_certs == 0:
            self.certificates_page.wait_for_first_certificate_button()
            self.certificates_page.click_first_certificate_button()
        else:
            self.certificates_page.wait_for_add_certificate_button()
            self.certificates_page.click_add_certificate_button()

        certificate = self.certificates_page.certificates[existing_certs]

        # Set the certificate properties
        certificate.course_title = course_title_override

        # add signatories
        added_signatories = 0
        for idx, signatory in enumerate(signatories):
            certificate.signatories[idx].name = signatory['name']
            certificate.signatories[idx].title = signatory['title']
            certificate.signatories[idx].organization = signatory['organization']
            certificate.signatories[idx].upload_signature_image('Signature-{}.png'.format(uuid.uuid4().hex[:4]))

            added_signatories += 1
            if len(signatories) > added_signatories:
                certificate.click_add_signatory_button()

        # Save the certificate
        self.assertEqual(certificate.get_text('.action-primary'), "Create")
        certificate.click_create_certificate_button()
        self.assertIn(course_title_override, certificate.course_title)
        return certificate

    def test_no_certificates_by_default(self):
        """
        Scenario: Ensure that message telling me to create a new certificate is
            shown when no certificate exist.
        Given I have a course without certificates
        When I go to the Certificates page in Studio
        Then I see "You have not created any certificates yet." message and
        a link with text "Set up your certificate"
        """
        self.certificates_page.visit()
        self.assertTrue(self.certificates_page.no_certificates_message_shown)
        self.assertIn(
            "You have not created any certificates yet.",
            self.certificates_page.no_certificates_message_text
        )
        self.assertIn(
            "Set up your certificate",
            self.certificates_page.new_certificate_link_text
        )

    def test_can_create_and_edit_certficate(self):
        """
        Scenario: Ensure that the certificates can be created and edited correctly.
        Given I have a course without certificates
        When I click button 'Add your first Certificate'
        And I set new the course title override and signatory and click the button 'Create'
        Then I see the new certificate is added and has correct data
        When I edit the  certificate
        And I change the name and click the button 'Save'
        Then I see the certificate is saved successfully and has the new name
        """
        self.certificates_page.visit()
        self.certificates_page.wait_for_first_certificate_button()
        certificate = self.create_and_verify_certificate(
            "Course Title Override",
            0,
            [self.make_signatory_data('first'), self.make_signatory_data('second')]
        )

        # Edit the certificate
        certificate.click_edit_certificate_button()
        certificate.course_title = "Updated Course Title Override 2"
        self.assertEqual(certificate.get_text('.action-primary'), "Save")
        certificate.click_save_certificate_button()

        self.assertIn("Updated Course Title Override 2", certificate.course_title)

    def test_can_delete_certificate(self):
        """
        Scenario: Ensure that the user can delete certificate.
        Given I have a course with 1 certificate
        And I go to the Certificates page
        When I delete the Certificate with name "New Certificate"
        Then I see that there is no certificate
        When I refresh the page
        Then I see that the certificate has been deleted
        """
        self.certificates_page.visit()
        certificate = self.create_and_verify_certificate(
            "Course Title Override",
            0,
            [self.make_signatory_data('first'), self.make_signatory_data('second')]
        )

        certificate.wait_for_certificate_delete_button()

        self.assertEqual(len(self.certificates_page.certificates), 1)

        # Delete the certificate we just created
        certificate.click_delete_certificate_button()
        self.certificates_page.click_confirmation_prompt_primary_button()

        # Reload the page and confirm there are no certificates
        self.certificates_page.visit()
        self.assertEqual(len(self.certificates_page.certificates), 0)

    def test_can_create_and_edit_signatories_of_certficate(self):
        """
        Scenario: Ensure that the certificates can be created with signatories and edited correctly.
        Given I have a course without certificates
        When I click button 'Add your first Certificate'
        And I set new the course title override and signatory and click the button 'Create'
        Then I see the new certificate is added and has one signatory inside it
        When I click 'Edit' button of signatory panel
        And I set the name and click the button 'Save' icon
        Then I see the signatory name updated with newly set name
        When I refresh the certificates page
        Then I can see course has one certificate with new signatory name
        When I click 'Edit' button of signatory panel
        And click on 'Close' button
        Then I can see no change in signatory detail
        """
        self.certificates_page.visit()
        certificate = self.create_and_verify_certificate(
            "Course Title Override",
            0,
            [self.make_signatory_data('first')]
        )
        self.assertEqual(len(self.certificates_page.certificates), 1)
        # Edit the signatory in certificate
        signatory = certificate.signatories[0]
        signatory.edit()

        signatory.name = 'Updated signatory name'
        signatory.title = 'Update signatory title'
        signatory.organization = 'Updated signatory organization'
        signatory.save()

        self.assertEqual(len(self.certificates_page.certificates), 1)

        #Refreshing the page, So page have the updated certificate object.
        self.certificates_page.refresh()
        self.certificates_page.wait_for_page()
        signatory = self.certificates_page.certificates[0].signatories[0]
        self.assertIn("Updated signatory name", signatory.name)
        self.assertIn("Update signatory title", signatory.title)
        self.assertIn("Updated signatory organization", signatory.organization)

        signatory.edit()
        signatory.close()

        self.assertIn("Updated signatory name", signatory.name)

    def test_can_cancel_creation_of_certificate(self):
        """
        Scenario: Ensure that creation of a certificate can be canceled correctly.
        Given I have a course without certificates
        When I click button 'Add your first Certificate'
        And I set name of certificate and click the button 'Cancel'
        Then I see that there is no certificates in the course
        """
        self.certificates_page.visit()
        self.certificates_page.click_first_certificate_button()
        certificate = self.certificates_page.certificates[0]
        certificate.course_title = "Title Override"
        certificate.click_cancel_edit_certificate()
        self.assertEqual(len(self.certificates_page.certificates), 0)

    def test_line_breaks_in_signatory_title(self):
        """
        Scenario: Ensure that line breaks are properly reflected in certificate

        Given I have a certificate with signatories
        When I add signatory title with new line character
        Then I see line break in certificate title
        """
        self.certificates_page.visit()
        certificate = self.create_and_verify_certificate(
            "Course Title Override",
            0,
            [
                {
                    'name': 'Signatory Name',
                    'title': 'Signatory title with new line character \n',
                    'organization': 'Signatory Organization',
                }
            ]
        )

        certificate.wait_for_certificate_delete_button()

        # Make sure certificate is created
        self.assertEqual(len(self.certificates_page.certificates), 1)

        signatory_title = self.certificates_page.get_first_signatory_title()
        self.assertNotEqual([], re.findall(r'<br\s*/?>', signatory_title))

    def test_course_number_in_certificate_details_view(self):
        """
        Scenario: Ensure that Course Number is displayed in certificate details view

        Given I have a certificate
        When I visit certificate details page on studio
        Then I see Course Number next to Course Name
        """
        self.certificates_page.visit()
        certificate = self.create_and_verify_certificate(
            "Course Title Override",
            0,
            [self.make_signatory_data('first')]
        )

        certificate.wait_for_certificate_delete_button()

        # Make sure certificate is created
        self.assertEqual(len(self.certificates_page.certificates), 1)
        course_number = self.certificates_page.get_course_number()
        self.assertEqual(self.course_info['number'], course_number)

    def test_course_number_override_in_certificate_details_view(self):
        """
        Scenario: Ensure that Course Number Override is displayed in certificate details view

        Given I have a certificate
        When I visit certificate details page on studio then course number override should be hidden.
        Then I visit the course advance settings page and set the value for course override number.
        Then I see Course Number Override next to Course Name in certificate settings page.
        """

        self.course_advanced_settings.update(
            {'Course Number Display String': 'Course Number Override String'}
        )

        self.certificates_page.visit()
        certificate = self.create_and_verify_certificate(
            "Course Title Override",
            0,
            [self.make_signatory_data('first')]
        )
        self.assertFalse(self.certificates_page.course_number_override().present)
        certificate.wait_for_certificate_delete_button()

        # Make sure certificate is created
        self.assertEqual(len(self.certificates_page.certificates), 1)

        # set up course number override in Advanced Settings Page
        self.advanced_settings_page.visit()
        self.advanced_settings_page.set_values(self.course_advanced_settings)
        self.advanced_settings_page.wait_for_ajax()

        self.certificates_page.visit()
        course_number_override = self.certificates_page.get_course_number_override()
        self.assertEqual(self.course_advanced_settings['Course Number Display String'], course_number_override)
        self.assertTrue(self.certificates_page.course_number_override().present)
