"""
Course Certificates pages.
"""
from bok_choy.promise import EmptyPromise
from .course_page import CoursePage


class CertificatesPage(CoursePage):
    """
    Course certificates page.
    """

    url_path = "certificates"
    certficate_css = ".certificates-list"

    def is_browser_on_page(self):
        """
        Verify that the browser is on the page and it is not still loading.
        """
        EmptyPromise(
            lambda: self.q(css='body.view-certificates').present,
            'On the certificates page'
        ).fulfill()

        EmptyPromise(
            lambda: not self.q(css='span.spin').visible,
            'Certificates are finished loading'
        ).fulfill()

        return True

    @property
    def certificates(self):
        """
        Return list of the certificates for the course.
        """
        css = self.certficate_css + ' .wrapper-collection'
        return [Certificate(self, self.certficate_css, index) for index in xrange(len(self.q(css=css)))]

    def create_first_certificate(self):
        """
        Creates new certificate when there are none initially defined.
        """
        self.q(css=self.certficate_css + " .new-button").first.click()

    def add_certificate(self):
        """
        Creates new certificate when at least one already exists
        """
        self.q(css=self.certficate_css + " .action-add").first.click()

    def wait_for_confirmation_prompt(self):
        """
        Show confirmation prompt
        We can't use confirm_prompt because its wait_for_notification is flaky when asynchronous operation
        completed very quickly.
        """
        self.wait_for_element_visibility('.prompt', 'Prompt is visible')
        self.wait_for_element_visibility('.prompt .action-primary', 'Confirmation button is visible')

    @property
    def no_certificates_message_shown(self):
        """
        Returns whether or not no certificates created message is present.
        """
        return self.q(css='.wrapper-content ' + self.certficate_css + ' .no-content').present

    @property
    def no_certificates_message_text(self):
        """
        Returns text of .no-content container.
        """
        return self.q(css='.wrapper-content ' + self.certficate_css + ' .no-content').text[0]


class Certificate(object):
    """
    Certificate wrapper.
    """

    def __init__(self, page, prefix, index):
        self.page = page
        self.selector = prefix + ' .certificates-list-item-{}'.format(index)
        self.index = index

    def get_selector(self, css=''):
        """
        Return selector fo certificate container
        """
        return ' '.join([self.selector, css])

    def find_css(self, css_selector):
        """
        Find elements as defined by css locator.
        """
        return self.page.q(css=self.get_selector(css=css_selector))

    def toggle(self):
        """
        Expand/collapse certificate configuration.
        """
        self.find_css('a.detail-toggle').first.click()

    @property
    def signatories(self):
        """
        Return list of the signatories for the certificate.
        """
        css = self.selector + ' .signatory-' + self.mode
        return [Signatory(self, self.selector, self.mode, index) for index in xrange(len(self.page.q(css=css)))]

    @property
    def is_expanded(self):
        """
        Certificate details are expanded.
        """
        return self.find_css('a.detail-toggle.hide-details').present

    def get_text(self, css):
        """
        Return text for the defined by css locator.
        """
        return self.find_css(css).first.text[0]

    def edit(self):
        """
        Open editing view for the certificate.
        """
        self.find_css('.action-edit .edit').first.click()

    @property
    def delete_button_is_present(self):
        """
        Returns whether or not the delete icon is present.
        """
        return self.find_css('.actions .delete').present

    def delete_certificate(self):
        """
        Delete the certificate
        """
        # pylint: disable=pointless-statement
        self.delete_button_is_present
        self.find_css('.actions .delete').first.click()
        self.page.wait_for_confirmation_prompt()
        self.find_css('.action-primary').first.click()
        self.page.wait_for_ajax()

    def save(self):
        """
        Save certificate.
        """
        self.find_css('.action-primary').first.click()
        self.page.wait_for_ajax()

    def cancel(self):
        """
        Cancel certificate editing.
        """
        self.find_css('.action-secondary').first.click()

    def add_signatory(self):
        """
        Add signatory to certificate
        """
        self.find_css('.action-add-signatory').first.click()

    @property
    def validation_message(self):
        """
        Return validation message.
        """
        return self.get_text('.message-status.error')

    @property
    def mode(self):
        """
        Return certificate mode.
        """
        if self.find_css('.collection-edit').present:
            return 'edit'
        elif self.find_css('.collection').present:
            return 'details'

    @property
    # pylint: disable=invalid-name
    def id(self):
        """
        Returns certificate id.
        """
        return self.get_text('.certificate-id .certificate-value')

    @property
    def name(self):
        """
        Return certificate name.
        """
        return self.get_text('.title')

    @name.setter
    def name(self, value):
        """
        Set certificate name.
        """
        self.find_css('.collection-name-input').first.fill(value)

    @property
    def description(self):
        """
        Return certificate description.
        """
        return self.get_text('.certificate-description')

    @description.setter
    def description(self, value):
        """
        Set certificate description.
        """
        self.find_css('.certificate-description-input').first.fill(value)


class Signatory(object):
    """
    Signatory wrapper.
    """

    def __init__(self, certificate, prefix, mode, index):
        self.certificate = certificate
        self.prefix = prefix
        self.index = index
        self.mode = mode

    def get_selector(self, css=''):
        """
        Return selector fo signatory container
        """
        selector = self.prefix + ' .signatory-{}-view-{}'.format(self.mode, self.index)
        return ' '.join([selector, css])

    def find_css(self, css_selector):
        """
        Find elements as defined by css locator.
        """
        return self.certificate.page.q(css=self.get_selector(css=css_selector))

    @property
    def name(self):
        """
        Return signatory name.
        """
        return self.find_css('.signatory-panel-body .signatory-name-value').first.text[0]

    @name.setter
    def name(self, value):
        """
        Set signatory name.
        """
        self.find_css('.signatory-name-input').first.fill(value)

    @property
    def title(self):
        """
        Return signatory title.
        """
        return self.find_css('.signatory-panel-body .signatory-title-value').first.text[0]

    @title.setter
    def title(self, value):
        """
        Set signatory title.
        """
        self.find_css('.signatory-title-input').first.fill(value)

    @property
    def organization(self):
        """
        Return signatory organization.
        """
        return self.find_css('.signatory-panel-body .signatory-organization-value').first.text[0]

    @organization.setter
    def organization(self, value):
        """
        Set signatory organization.
        """
        self.find_css('.signatory-organization-input').first.fill(value)

    def edit(self):
        """
        Open editing view for the signatory.
        """
        self.find_css('.edit-signatory').first.click()
        self.mode = 'edit'
        self.wait_for_signatory_edit_view()

    def delete_signatory(self):
        """
        Delete the signatory
        """
        # pylint: disable=pointless-statement
        self.delete_icon_is_present
        self.find_css('.signatory-panel-delete').first.click()
        self.wait_for_signatory_delete_prompt()

        self.certificate.page.q(css='#prompt-warning a.button.action-primary').first.click()
        self.certificate.page.wait_for_ajax()

    def save(self):
        """
        Save signatory.
        """
        # Move focus from input to save button and then click it
        self.certificate.page.browser.execute_script(
            "$('{} .signatory-panel-save').focus()".format(self.get_selector())
        )
        self.find_css('.signatory-panel-save').first.click()
        self.mode = 'details'
        self.certificate.page.wait_for_ajax()
        self.wait_for_signatory_detail_view()

    def close(self):
        """
        Cancel signatory editing.
        """
        self.find_css('.signatory-panel-close').first.click()
        self.mode = 'details'
        self.wait_for_signatory_detail_view()

    @property
    def delete_icon_is_present(self):
        """
        Returns whether or not the delete icon is present.
        """
        return self.find_css('.signatory-panel-delete').present

    def wait_for_signatory_delete_prompt(self):
        """
        Promise to wait until signatory delete prompt is visible
        """
        EmptyPromise(
            lambda: self.certificate.page.q(css='a.button.action-primary').present,
            'Delete prompt is displayed'
        ).fulfill()

    def wait_for_signatory_edit_view(self):
        """
        Promise to wait until signatory edit view is loaded
        """
        EmptyPromise(
            lambda: self.find_css('.signatory-panel-body .signatory-name-input').present,
            'On signatory edit view'
        ).fulfill()

    def wait_for_signatory_detail_view(self):
        """
        Promise to wait until signatory details view is loaded
        """
        EmptyPromise(
            lambda: self.find_css('.signatory-panel-body .signatory-name-value').present,
            'On signatory details view'
        ).fulfill()
