# -*- coding: utf-8 -*-
"""
Management commands for third_party_auth
"""
import datetime
import dateutil.parser
from django.core.management.base import BaseCommand, CommandError
from lxml import etree
import requests
from onelogin.saml2.utils import OneLogin_Saml2_Utils
from third_party_auth.models import SAMLConfiguration, SAMLProviderConfig, SAMLProviderData

#pylint: disable=superfluous-parens,no-member


class MetadataParseError(Exception):
    """ An error occurred while parsing the SAML metadata from an IdP """
    pass


class Command(BaseCommand):
    """ manage.py commands to manage SAML/Shibboleth SSO """
    help = '''Configure/maintain/update SAML-based SSO'''

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("saml requires one argument: pull")

        if not SAMLConfiguration.is_enabled():
            self.stdout.write("Warning: SAML support is disabled via SAMLConfiguration.\n")

        subcommand = args[0]

        if subcommand == "pull":
            self.cmd_pull()
        else:
            raise CommandError("Unknown argment: {}".format(subcommand))

    @staticmethod
    def tag_name(tag_name):
        """ Get the namespaced-qualified name for an XML tag """
        return '{urn:oasis:names:tc:SAML:2.0:metadata}' + tag_name

    def cmd_pull(self):
        """ Fetch the metadata for each provider and update the DB """
        # First make a list of all the metadata XML URLs:
        url_map = {}
        for idp_slug in SAMLProviderConfig.key_values('idp_slug', flat=True):
            config = SAMLProviderConfig.current(idp_slug)
            if not config.enabled:
                continue
            url = config.metadata_source
            if url not in url_map:
                url_map[url] = []
            if config.entity_id not in url_map[url]:
                url_map[url].append(config.entity_id)
        # Now fetch the metadata:
        for url, entity_ids in url_map.items():
            try:
                self.stdout.write("\n→ Fetching {}\n".format(url))
                if not url.lower().startswith('https'):
                    self.stdout.write("→ WARNING: This URL is not secure! It should use HTTPS.\n")
                response = requests.get(url, verify=True)  # May raise HTTPError or SSLError or ConnectionError
                response.raise_for_status()  # May raise an HTTPError

                try:
                    parser = etree.XMLParser(remove_comments=True)
                    xml = etree.fromstring(response.text, parser)
                except etree.XMLSyntaxError:
                    raise
                # TODO: Can use OneLogin_Saml2_Utils to validate signed XML if anyone is using that

                for entity_id in entity_ids:
                    self.stdout.write("→ Processing IdP with entityID {}\n".format(entity_id))
                    public_key, sso_url, expires_at = self._parse_metadata_xml(xml, entity_id)
                    self._update_data(entity_id, public_key, sso_url, expires_at)
            except Exception as err:  # pylint: disable=broad-except
                self.stderr.write(u"→ ERROR: {}\n\n".format(err.message))

    @classmethod
    def _parse_metadata_xml(cls, xml, entity_id):
        """
        Given an XML document containing SAML 2.0 metadata, parse it and return a tuple of
        (public_key, sso_url, expires_at) for the specified entityID.

        Raises MetadataParseError if anything is wrong.
        """
        if xml.tag == cls.tag_name('EntityDescriptor'):
            entity_desc = xml
        else:
            if xml.tag != cls.tag_name('EntitiesDescriptor'):
                raise MetadataParseError("Expected root element to be <EntitiesDescriptor>, not {}".format(xml.tag))
            entity_desc = xml.find(".//{}[@entityID='{}']".format(cls.tag_name('EntityDescriptor'), entity_id))
            if not entity_desc:
                raise MetadataParseError("Can't find EntityDescriptor for entityID {}".format(entity_id))

        expires_at = None
        if "validUntil" in xml.attrib:
            expires_at = dateutil.parser.parse(xml.attrib["validUntil"])
        if "cacheDuration" in xml.attrib:
            cache_expires = OneLogin_Saml2_Utils.parse_duration(xml.attrib["cacheDuration"])
            if expires_at is None or cache_expires < expires_at:
                expires_at = cache_expires

        sso_desc = entity_desc.find(cls.tag_name("IDPSSODescriptor"))
        if not sso_desc:
            raise MetadataParseError("IDPSSODescriptor missing")
        if 'urn:oasis:names:tc:SAML:2.0:protocol' not in sso_desc.get("protocolSupportEnumeration"):
            raise MetadataParseError("This IdP does not support SAML 2.0")

        # Now we just need to get the public_key and sso_url
        public_key = sso_desc.findtext("./{}//{}".format(
            cls.tag_name("KeyDescriptor"), "{http://www.w3.org/2000/09/xmldsig#}X509Certificate"
        ))
        if not public_key:
            raise MetadataParseError("Public Key missing. Expected an <X509Certificate>")
        public_key = public_key.replace(" ", "")
        binding_elements = sso_desc.iterfind("./{}".format(cls.tag_name("SingleSignOnService")))
        sso_bindings = {element.get('Binding'): element.get('Location') for element in binding_elements}
        try:
            # The only binding supported by python-saml and python-social-auth is HTTP-Redirect:
            sso_url = sso_bindings['urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect']
        except KeyError:
            raise MetadataParseError("Unable to find SSO URL with HTTP-Redirect binding.")
        return public_key, sso_url, expires_at

    def _update_data(self, entity_id, public_key, sso_url, expires_at):
        """
        Update/Create the SAMLProviderData for the given entity ID.
        """
        data_obj = SAMLProviderData.current(entity_id)
        fetched_at = datetime.datetime.now()
        if data_obj and (data_obj.public_key == public_key and data_obj.sso_url == sso_url):
            data_obj.expires_at = expires_at
            data_obj.fetched_at = fetched_at
            data_obj.save()
            self.stdout.write("→ Updated existing SAMLProviderData. Nothing has changed.\n")
        else:
            SAMLProviderData.objects.create(
                entity_id=entity_id,
                fetched_at=fetched_at,
                expires_at=expires_at,
                sso_url=sso_url,
                public_key=public_key,
            )
            self.stdout.write("→ Created new record for SAMLProviderData\n")
