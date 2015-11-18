"""
Test the views served by third_party_auth.
"""
# pylint: disable=no-member
import ddt
from lxml import etree
import unittest
from .testutil import AUTH_FEATURE_ENABLED, SAMLTestCase

# Define some XML namespaces:
from third_party_auth.tasks import SAML_XML_NS
XMLDSIG_XML_NS = 'http://www.w3.org/2000/09/xmldsig#'


@unittest.skipUnless(AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
@ddt.ddt
class SAMLMetadataTest(SAMLTestCase):
    """
    Test the SAML metadata view
    """
    METADATA_URL = '/auth/saml/metadata.xml'

    def test_saml_disabled(self):
        """ When SAML is not enabled, the metadata view should return 404 """
        self.enable_saml(enabled=False)
        response = self.client.get(self.METADATA_URL)
        self.assertEqual(response.status_code, 404)

    @ddt.data('saml_key', 'saml_key_alt')  # Test two slightly different key pair export formats
    def test_metadata(self, key_name):
        self.enable_saml()
        doc = self._fetch_metadata()
        # Check the ACS URL:
        acs_node = doc.find(".//{}".format(etree.QName(SAML_XML_NS, 'AssertionConsumerService')))
        self.assertIsNotNone(acs_node)
        self.assertEqual(acs_node.attrib['Location'], 'http://example.none/auth/complete/tpa-saml/')

    def test_default_contact_info(self):
        self.enable_saml()
        self.check_metadata_contacts(
            xml=self._fetch_metadata(),
            tech_name="edX Support",
            tech_email="technical@example.com",
            support_name="edX Support",
            support_email="technical@example.com"
        )

    def test_custom_contact_info(self):
        self.enable_saml(
            other_config_str=(
                '{'
                '"TECHNICAL_CONTACT": {"givenName": "Jane Tech", "emailAddress": "jane@example.com"},'
                '"SUPPORT_CONTACT": {"givenName": "Joe Support", "emailAddress": "joe@example.com"}'
                '}'
            )
        )
        self.check_metadata_contacts(
            xml=self._fetch_metadata(),
            tech_name="Jane Tech",
            tech_email="jane@example.com",
            support_name="Joe Support",
            support_email="joe@example.com"
        )

    def test_signed_metadata(self):
        self.enable_saml(
            other_config_str='{"SECURITY_CONFIG": {"signMetadata": true} }',
        )
        doc = self._fetch_metadata()
        sig_node = doc.find(".//{}".format(etree.QName(XMLDSIG_XML_NS, 'SignatureValue')))
        self.assertIsNotNone(sig_node)

    def _fetch_metadata(self):
        """ Fetch and parse the metadata XML at self.METADATA_URL """
        response = self.client.get(self.METADATA_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/xml')
        # The result should be valid XML:
        try:
            metadata_doc = etree.fromstring(response.content)
        except etree.LxmlError:
            self.fail('SAML metadata must be valid XML')
        self.assertEqual(metadata_doc.tag, etree.QName(SAML_XML_NS, 'EntityDescriptor'))
        return metadata_doc

    def check_metadata_contacts(self, xml, tech_name, tech_email, support_name, support_email):
        """ Validate that the contact info in the metadata has the expected values """
        technical_node = xml.find(".//{}[@contactType='technical']".format(etree.QName(SAML_XML_NS, 'ContactPerson')))
        self.assertIsNotNone(technical_node)
        tech_name_node = technical_node.find(etree.QName(SAML_XML_NS, 'GivenName'))
        self.assertEqual(tech_name_node.text, tech_name)
        tech_email_node = technical_node.find(etree.QName(SAML_XML_NS, 'EmailAddress'))
        self.assertEqual(tech_email_node.text, tech_email)

        support_node = xml.find(".//{}[@contactType='support']".format(etree.QName(SAML_XML_NS, 'ContactPerson')))
        self.assertIsNotNone(support_node)
        support_name_node = support_node.find(etree.QName(SAML_XML_NS, 'GivenName'))
        self.assertEqual(support_name_node.text, support_name)
        support_email_node = support_node.find(etree.QName(SAML_XML_NS, 'EmailAddress'))
        self.assertEqual(support_email_node.text, support_email)
