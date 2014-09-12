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

from django.conf import settings


class License(object):
    """
    Base License class
    """

    def __init__(self, license=None, version=None):
        """
        Construct a new license object
        """
        self.license = license
        self.version = version

        self.text = ""

    @property
    def img_url(self):
        """
        Stub property for img_url
        """

        return ""

    def __str__(self):
        """
        Return a string representation of the license
        """
        return self.license

    def __get__(self, instance, owner):
        return instance

    def __set__(self, instance, value):
        """
        Define a setter so the `license` property can be modified by setting the instance to a valid license String
        """
        instance.license = value

    def img(self, big=False):
        """
        Return a piece of html with a reference to a license image
        """

        if not self.license:
            return _("No license.")

        if (big):
            img_size = "88x31"
        else:
            img_size = "80x15"

        img = "<img src='{img_url}/{img_size}.png' />".format(
            img_url=self.img_url,
            img_size=img_size
        )

        return img

    @property
    def small_img(self):
        """
        Alias for `img(big=False)`
        """
        return self.img(big=False)

    @property
    def large_img(self):
        """
        Alias for `img(big=True)`
        """
        return self.img(big=True)

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
        return {"license": value.license, "license_version": value.version}

    def from_json(self, license_dict):
        """
        Construct a new license object from a valid JSON representation
        """
        return parse_license(license_dict.get('license'), license_dict.get('version'))


class ARRLicense(License):
    """
    License class for an 'All rights reserved' license
    """

    def __init__(self, *args, **kwargs):
        super(ARRLicense, self).__init__(*args, **kwargs)

    @property
    def img_url(self):
        """
        Return the image base url for an 'All rights Reserved'
        """

        return settings.STATIC_URL + "images/arr/"

    @property
    def html(self):
        """
        Return a piece of html that descripts the license
        """

        phrase = _("All rights are reserved for this work.")

        return "<p>{phrase}<br/>{img}</p>".format(
            phrase=phrase,
            img=self.img(big=True)
        )


class CCLicense(License):
    """
    License class for a Creative Commons license
    """

    def __init__(self, *args, **kwargs):
        super(CCLicense, self).__init__(*args, **kwargs)

        # If no version was set during initialization, we may assume the most recent version of a CC license and fetch that using the API
        if self.license and not self.version:
            data = CCLicense.get_cc_api_data(self.license)
            license_img = data.find(".//a")
            self.version = license_img.get("href").split("/")[-2]

    @property
    def img_url(self):
        if self.license == "CC0":
            license_string = "zero/1.0"
        else:
            # The Creative Commons License is stored as a string formatted in the following way: 'CC-BY-SA'. First it is converted to lowercase.
            # The split and join serve to remove the 'CC-' from the beginning of the license string.

            license = self.license.lower()
            attrs = license.split("-")
            attrs = attrs[1:]
            license = "-".join(attrs)

            license_string = "{license}/{version}/".format(
                license=license,
                version=self.version
            )

        img_url = "http://i.creativecommons.org/l/{license}".format(
            license=license_string
        )

        return img_url

    @property
    def html(self):
        """
        Return a piece of html that describes the license
        """

        html = "<p>{description}<br />{image}</p>".format(
            description=self.description,
            image=self.large_img
        )

        return html

    @property
    def description(self):
        """
        Return a text that describes the license
        """

        # If the text hasn't been stored already, fetch it using the API
        if not self.text:
            data = CCLicense.get_cc_api_data(self.license)

            # Change the tag to be a paragraph
            data.tag = "p"

            # Remove the image from the API response
            img = data.find(".//a")
            img.getparent().remove(img)

            # And convert the html to a string
            self.text = etree.tostring(data, method="html")

        return self.text

    @staticmethod
    def cc_attributes_from_license(license):
        """
        Convert a license object to a tuple of values representing the relevant CC attributes

        The returning tuple contains a string and two boolean values which represent:
          - The license class, either 'zero' or 'standard'
          - Are commercial applications of the content allowed, 'yes', 'no' or 'only under the same license' (share alike)
          - Are derivatives of the content allowed, 'true' by default
        """
        commercial = "y"
        derivatives = "y"

        if license == "CC0":
            license_class = "zero"
        else:
            license_class = "standard"

            # Split the license attributes and remove the 'CC-' from the beginning of the string
            l = iter(license.split("-")[1:])

            # Then iterate over the remaining attributes that are set
            for s in l:
                if s == "SA":
                    derivatives = "sa"
                elif s == "NC":
                    commercial = "n"
                elif s == "ND":
                    derivatives = "n"

        return (license_class,commercial,derivatives)

    @staticmethod
    def get_cc_api_data(license):
        """
        Fetch data about a CC license using the API at creativecommons.org
        """
        (license_class,commercial,derivatives) = CCLicense.cc_attributes_from_license(license)

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

def parse_license(license, version=None):
    """
    Return a license object appropriate to the license

    This is a simple utility function to allowed for easy conversion between license strings and license objects. It
    accepts a license string and an optional license version and returns the corresponding license object. It also accounts
    for the license parameter already being a license object.
    """

    if not license:
        return License(license, version)
    elif isinstance(license, License):
        return license
    elif license == "ARR":
        return ARRLicense(license,version)
    elif license[0:5] == "CC-BY" or license == "CC0":
        return CCLicense(license,version)
    else:
        raise ValueError('Invalid license.')