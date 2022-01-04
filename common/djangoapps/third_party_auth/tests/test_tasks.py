"""
Unit tests for third party auth tasks
"""


from unittest import TestCase
from common.lib.safe_lxml.safe_lxml import etree

from common.djangoapps.third_party_auth.tasks import parse_metadata_xml


class TestThirdPartyAuthTasks(TestCase):
    def test_parse_metadata_uses_signing_cert(self):
        entity_id = 'http://testid'
        parser = etree.XMLParser(remove_comments=True)
        xml_text = '''
            <?xml version="1.0"?>
            <md:EntityDescriptor xmlns:md="urn:oasis:names:tc:SAML:2.0:metadata" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" entityID="http://testid">
                <md:IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
                    <md:KeyDescriptor use="signing">
                        <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                            <ds:X509Data>
                            <ds:X509Certificate>abc+hkIuUktxkg=</ds:X509Certificate>
                            </ds:X509Data>
                        </ds:KeyInfo>
                    </md:KeyDescriptor>
                    <md:KeyDescriptor use="encryption">
                        <ds:KeyInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                            <ds:X509Data>
                            <ds:X509Certificate>blachabc+hkIuUktxkg=blaal;skdjf;ksd</ds:X509Certificate>
                            </ds:X509Data>
                        </ds:KeyInfo>
                    </md:KeyDescriptor>
                </md:IDPSSODescriptor>
            </md:EntityDescriptor>
        '''
        xml = etree.fromstring(xml_text, parser)
        public_key, _, _ = parse_metadata_xml(xml, entity_id)
        assert public_key == 'abc+hkIuUktxkg='
