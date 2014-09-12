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
from json.encoder import JSONEncoder

from django.conf import settings

edx_xml_parser = etree.XMLParser(
    dtd_validation=False, 
    load_dtd=False,
    remove_comments=True, 
    remove_blank_text=True
)

class License(list):
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
        self.img_url = ""

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
            img_size = "88x31";
        else:
            img_size = "80x15"  
        
        img = "<img src='{img_url}{img_size}.png' />".format(img_url = self.img_url, img_size=img_size)

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
    def __init__(self, *args, **kwargs):
        super(ARRLicense, self).__init__(*args, **kwargs)

        self.img_url = settings.STATIC_URL + "images/arr/"
    
    @property
    def html(self):
        """
        Return a piece of html that descripts the license
        """

        phrase = _("All rights are reserved for this work.")
        return "<p>{phrase}<br/>{img}</p>".format(phrase=phrase, img=self.img(big=True))
        

class CCLicense(License):
    def __init__(self, *args, **kwargs):
        super(CCLicense, self).__init__(*args, **kwargs)

        if self.license and not(self.version):
            data = CCLicense.get_cc_api_data(self.license)
            license_img = data.find(".//a")
            self.version = license_img.get("href").split("/")[-2]

        if self.license == "CC0":
            self.img_url = "http://i.creativecommons.org/l/zero/"+self.version+"/"
        else:
            self.img_url = 'http://i.creativecommons.org/l/' + "-".join(self.license.lower().split("-")[1:]) + "/"+self.version+"/"
    
    @property
    def html(self, bigImage=True):
        """
        Return a piece of html that describes the license
        """

        return "<p>" + self.description + "<br/>" + self.img(bigImage) + "</p>"

    @property
    def description(self):
        """
        Return a text that describes the license
        """

        if not(self.text):
            data = CCLicense.get_cc_api_data(self.license)
            data.tag = "p"

            img = data.find(".//a")
            img.getparent().remove(img)

            self.text = etree.tostring(data, method="html")

        return self.text

    @staticmethod
    def cc_attributes_from_license(license):
        commercial = "y";
        derivatives = "y";

        if license == "CC0":
            license_class = "zero"
        else:
            license_class = "standard"
        
            l = iter(license.split("-")[1:])

            for s in l:
                if (s=="SA"):
                    derivatives = "sa";
                elif (s=="NC"):
                    commercial = "n";
                elif (s=="ND"):
                    derivatives= "n";

        return (license_class,commercial,derivatives)
    
    @staticmethod
    def get_cc_api_data(license):
        (license_class,commercial,derivatives) = CCLicense.cc_attributes_from_license(license)

        url = "http://api.creativecommons.org/rest/1.5/license/"+license_class+"/get?commercial="+commercial+"&derivatives="+derivatives
        xml_data = requests.get(url).content

        license_file = StringIO(xml_data.encode('ascii', 'ignore'))
        xml_obj = etree.parse(license_file, parser=edx_xml_parser).getroot()
        data = xml_obj.find("html")

        return data

def parse_license(license, version=None):
    """
    Return a license object appropriate to the license
    """

    if not(license):
        return License(license, version);
    elif isinstance(license, License):
        return license
    elif license == "ARR":
        return ARRLicense(license,version)
    elif license[0:5] == "CC-BY" or license=="CC0":
        return CCLicense(license,version)
    else:
        raise ValueError('Invalid license.')