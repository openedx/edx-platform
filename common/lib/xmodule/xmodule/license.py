"""
Different types of licenses for content

This file contains a base license class as well as a some useful specific license classes, namely:
    - ARRLicense (All Rights Reserved License)
    - CCLicense (Creative Commons License)

The classes provide utility funcions for dealing with licensing, such as getting an image representation
of a license, a url to a page describing the specifics of the license, converting licenses to and from json
and storing some vital information about licenses, in particular the version.
"""
import requests
from cStringIO import StringIO
from lxml import etree
from django.utils.translation import ugettext as _

from xblock.fields import JSONField


class License(JSONField):
    """
    Base License class
    """

    _default = None
    MUTABLE = False

    def __init__(self, kind=None, version=None, *args, **kwargs):
        self.kind = kind
        self.version = version
        super(License, self).__init__(*args, **kwargs)

    @property
    def html(self):
        """
        Return a piece of html that describes the license

        This method should be overridden in child classes to provide the desired html.
        """
        return u"<p>" + _("This resource is not licensed.") + u"</p>"

    def to_json(self, value):
        """
        Return a JSON representation of the license
        """
        if value is None:
            return {"kind": "ARR", "version": "1.0"}
        elif isinstance(value, License):
            return {"kind": value.kind, "version": value.version}
        elif isinstance(value, dict) and 'kind' in value and 'version' in value:
            return {"kind": value['kind'], "version": value['version']}
        else:
            raise TypeError("Cannot convert {!r} to json".format(value))

    def from_json(self, field):
        """
        Construct a new license object from a valid JSON representation
        """
        if not field or field is "":
            return ARRLicense()
        elif isinstance(field, basestring):
            if field == "ARR":
                return ARRLicense()
            elif field[0:5] == "CC-BY" or field == "CC0":
                return CCLicense(field)
            else:
                raise ValueError('Invalid license.')
        elif isinstance(field, dict) and 'license' in field and 'version' in field:
            return parse_license(field['license'], field['version'])
        elif isinstance(field, dict) and 'kind' in field and 'version' in field:
            return parse_license(field['kind'], field['version'])
        elif isinstance(field, License):
            return field
        else:
            raise ValueError('Invalid license.')

    enforce_type = from_json


class ARRLicense(License):
    """
    License class for an 'All rights reserved' license
    """

    def __init__(self, kind="ARR", version=None, *args, **kwargs):
        super(ARRLicense, self).__init__(kind, version, *args, **kwargs)

    @property
    def html(self):
        """
        Return a piece of html that descripts the license
        """
        phrase = _("All rights reserved")
        return "&copy;<span class='license-text'>{phrase}</span>".format(
            phrase=phrase
        )


class CCLicense(License):
    """
    License class for a Creative Commons license
    """

    def __init__(self, kind, version=None, *args, **kwargs):
        super(CCLicense, self).__init__(kind, version, *args, **kwargs)
        # If no version was set during initialization, we may assume
        # the most recent version of a CC license and fetch
        # that using the API.
        if self.kind and not self.version:
            data = CCLicense.get_cc_api_data(self.kind)
            license_img = data.find(".//a")
            self.version = license_img.get("href").split("/")[-2]

    @property
    def html(self):
        """
        Return a piece of html that describes the license
        """

        license_html = ["<i class='icon-cc'></i>"]
        if 'CC0' in self.kind:
            license_html.append("<i class='icon-cc-zero'></i>")
        if 'BY' in self.kind:
            license_html.append("<i class='icon-cc-by'></i>")
        if 'NC' in self.kind:
            license_html.append("<i class='icon-cc-nc'></i>")
        if 'SA' in self.kind:
            license_html.append("<i class='icon-cc-sa'></i>")
        if 'ND' in self.kind:
            license_html.append("<i class='icon-cc-nd'></i>")

        phrase = _("Some rights reserved")
        return "<a rel='license' href='http://creativecommons.org/licenses/{license_link}/{version}/' " \
            "data-tooltip='{description}' target='_blank' class='license'>" \
            "{license_html}<span class='license-text'>{phrase}</span></a>".format(
                description=self.description,
                version=self.version,
                license_link=self.kind.lower()[3:],
                license_html=''.join(license_html),
                phrase=phrase
            )

    @property
    def description(self):
        """
        Return a text that describes the license
        """
        cc_attributes = []
        if 'BY' in self.kind:
            cc_attributes.append(_("Attribution"))
        if 'NC' in self.kind:
            cc_attributes.append(_("NonCommercial"))
        if 'SA' in self.kind:
            cc_attributes.append(_("ShareAlike"))
        if 'ND' in self.kind:
            cc_attributes.append(_("NonDerivatives"))

        return _("This work is licensed under a Creative Commons {attributes} {version} International License.").format(
            attributes='-'.join(cc_attributes),
            version=self.version
        )

    @staticmethod
    def cc_attributes_from_license(kind):
        """
        Convert a license object to a tuple of values representing the relevant CC attributes

        The returning tuple contains a string and two boolean values which represent:
          - The license class, either 'zero' or 'standard'
          - Are commercial applications of the content allowed, 'y' - yes, 'n' - no, or 'sa' - only under the same license (share alike)
          - Are derivatives of the content allowed, 'y' - yes, or 'n' - no. Default: 'y'
        """
        commercial = "y"
        derivatives = "y"

        if kind == "CC0":
            license_class = "zero"
        else:
            license_class = "standard"

            # Split the license attributes and remove the 'CC-' from the beginning of the string
            attrs = iter(kind.split("-")[1:])

            # Then iterate over the remaining attributes that are set
            for attr in attrs:
                if attr == "SA":
                    derivatives = "sa"
                elif attr == "NC":
                    commercial = "n"
                elif attr == "ND":
                    derivatives = "n"

        return (license_class, commercial, derivatives)

    @staticmethod
    def get_cc_api_data(kind):
        """
        Constructs the CC license according to the specification of creativecommons.org
        """
        (license_class, commercial, derivatives) = CCLicense.cc_attributes_from_license(kind)

        # Format the url for the particular license
        url = "http://api.creativecommons.org/rest/1.5/license/{license_class}/get?commercial={commercial}&derivatives={derivatives}".format(
            license_class=license_class,
            commercial=commercial,
            derivatives=derivatives
        )

        # Fetch the license data
        xml_data = requests.get(url).content

        # Set up the response parser
        edx_xml_parser = etree.XMLParser(
            dtd_validation=False,
            load_dtd=False,
            remove_comments=True,
            remove_blank_text=True
        )

        # Parse the response file and extract the relevant data
        license_file = StringIO(xml_data.encode('ascii', 'ignore'))
        xml_obj = etree.parse(
            license_file,
            parser=edx_xml_parser
        ).getroot()
        data = xml_obj.find("html")

        return data


def parse_license(kind_or_license, version=None):
    """
    Return a license object appropriate to the license

    This is a simple utility function to allowed for easy conversion between license strings and license objects. It
    accepts a license string and an optional license version and returns the corresponding license object. It also accounts
    for the license parameter already being a license object.
    """

    if kind_or_license is None or kind_or_license == "":
        return ARRLicense()
    elif isinstance(kind_or_license, License):
        return kind_or_license
    elif isinstance(kind_or_license, dict) and 'license' in kind_or_license and 'version' in kind_or_license:
        return parse_license(kind_or_license=kind_or_license['license'], version=kind_or_license['version'])
    elif isinstance(kind_or_license, dict) and 'kind' in kind_or_license and 'version' in kind_or_license:
        return parse_license(kind_or_license=kind_or_license['kind'], version=kind_or_license['version'])
    elif isinstance(kind_or_license, basestring):
        if kind_or_license == "ARR":
            return ARRLicense(kind_or_license, version)
        elif kind_or_license.startswith("CC-BY") or kind_or_license == "CC0":
            return CCLicense(kind_or_license, version)
    # If we get to this line, we found an invalid license. Lets raise an error.
    raise ValueError('Invalid license.')
