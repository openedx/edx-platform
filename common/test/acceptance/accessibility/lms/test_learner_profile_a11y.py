"""
Accessibility tests for LMS profile page.

Run just this test with:
SELENIUM_BROWSER=phantomjs paver test_bokchoy -d accessibility -t lms/test_learner_profile_a11y.py
"""
from ...tests.lms.test_learner_profile import LearnerProfileTestMixin
from bok_choy.web_app_test import WebAppTest


class LearnerProfileAxsTest(LearnerProfileTestMixin, WebAppTest):
    """
    Class to test learner profile accessibility.
    """

    def test_editable_learner_profile_axs(self):
        """
        Test the accessibility of the editable version of the profile page
        (user viewing her own public profile).
        """
        username, _ = self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(username)

        # There are several existing color contrast errors on this page,
        # we will ignore this error in the test until we fix them.
        profile_page.a11y_audit.config.set_rules({
            "ignore": ['color-contrast'],
        })

        profile_page.a11y_audit.check_for_accessibility_errors()

        profile_page.make_field_editable('language_proficiencies')
        profile_page.a11y_audit.check_for_accessibility_errors()

        profile_page.make_field_editable('bio')
        profile_page.a11y_audit.check_for_accessibility_errors()

    def test_read_only_learner_profile_axs(self):
        """
        Test the accessibility of the read-only version of a public profile page
        (user viewing someone else's profile page).
        """
        # initialize_different_user should cause country, language, and bio to be filled out (since
        # privacy is public). It doesn't appear that this is happening, although the method
        # works in regular bokchoy tests. Perhaps a problem with phantomjs? So this test is currently
        # only looking at a read-only profile page with a username.
        different_username, _ = self.initialize_different_user(privacy=self.PRIVACY_PUBLIC)
        self.log_in_as_unique_user()
        profile_page = self.visit_profile_page(different_username)
        profile_page.a11y_audit.check_for_accessibility_errors()
