"""
Course Certificates pages.
"""
from bok_choy.promise import EmptyPromise
from .course_page import CoursePage
from .utils import confirm_prompt


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

    def delete(self):
        """
        Delete the certificate
        """
        self.find_css('.actions .delete').first.click()
        confirm_prompt(self.page)
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
        self.selector = prefix + ' .signatory-{}-view-{}'.format(mode, index)
        self.index = index

    def get_selector(self, css=''):
        """
        Return selector fo signatory container
        """
        return ' '.join([self.selector, css])

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

    def edit(self):
        """
        Open editing view for the signatory.
        """
        self.find_css('.edit-signatory').first.click()

    def delete(self):
        """
        Delete the signatory
        """
        self.find_css('.signatory-panel-delete').first.click()
        confirm_prompt(self.certificate.page)
        self.certificate.page.wait_for_ajax()

    def save(self):
        """
        Save signatory.
        """
        self.find_css('.signatory-panel-save').first.click()
        self.certificate.page.wait_for_ajax()

    def close(self):
        """
        Cancel signatory editing.
        """
        self.find_css('.signatory-panel-close').first.click()
        EmptyPromise(
            lambda: self.find_css('.signatory-panel-body .signatory-name-value').present,
            'On signatory detail view'
        ).fulfill()

    @property
    def delete_icon_is_present(self):
        """
        Returns whether or not the delete icon is present.
        """
        return self.find_css('.signatory-panel-delete').present
