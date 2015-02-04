"""
Different types of licenses for content

This file contains a base license class as well as a some useful specific license classes, namely:
    - ARRLicense (All Rights Reserved License)
    - CCLicense (Creative Commons License)

The classes provide utility funcions for dealing with licensing, such as getting an image representation
of a license, a url to a page describing the specifics of the license, converting licenses to and from json
and storing some vital information about licenses, in particular the version.
"""
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
        return parse_license(field)

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
            self.version = "4.0"

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


def parse_license(kind_or_license, version=None):
    """
    Return a license object appropriate to the license

    This is a simple utility function to allow for easy conversion between
    license strings and license objects. It accepts a license string and an
    optional license version and returns the corresponding license object.
    It also accounts for the license parameter already being a license object.
    """

    if not kind_or_license:
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
        elif kind_or_license.startswith("CC"):
            return CCLicense(kind_or_license, version)
    # If we get to this line, we found an invalid license. Lets raise an error.
    raise ValueError('Invalid license.')
