"""
Pages object for the Django's /admin/ views.
"""
from bok_choy.page_object import PageObject
from common.test.acceptance.pages.lms import BASE_URL


class ChangeUserAdminPage(PageObject):
    """
    Change user page in Django's admin.
    """
    def __init__(self, browser, user_pk):
        super(ChangeUserAdminPage, self).__init__(browser)
        self.user_pk = user_pk

    @property
    def url(self):
        """
        Returns the page URL for the page based on self.user_pk.
        """

        return u'{base}/admin/auth/user/{user_pk}/'.format(
            base=BASE_URL,
            user_pk=self.user_pk,
        )

    @property
    def username(self):
        """
        Reads the read-only username.
        """
        return self.q(css='.field-username .readonly').text[0]

    @property
    def first_name_element(self):
        """
        Selects the first name element.
        """
        return self.q(css='[name="first_name"]')

    @property
    def first_name(self):
        """
        Reads the first name value from the input field.
        """
        return self.first_name_element.attrs('value')[0]

    @property
    def submit_element(self):
        """
        Gets the "Save" submit element.

        Note that there are multiple submit elements in the change view.
        """
        return self.q(css='input.default[type="submit"]')

    def submit(self):
        """
        Submits the form.
        """
        self.submit_element.click()

    def change_first_name(self, first_name):
        """
        Changes the first name and submits the form.

        Args:
            first_name: The first name as unicode.

        """

        self.first_name_element.fill(first_name)
        self.submit()

    def is_browser_on_page(self):
        """
        Returns True if the browser is currently on the right page.
        """
        return self.q(css='#user_form').present
