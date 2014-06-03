"""
Annotations Tool Mixin
This file contains global variables and functions used in the various Annotation Tools.
"""
from lxml import etree
from urlparse import urlparse
from os.path import splitext, basename
from HTMLParser import HTMLParser
from xblock.core import Scope, String

# Make '_' a no-op so we can scrape strings
_ = lambda text: text

def get_instructions(xmltree):
    """ Removes <instructions> from the xmltree and returns them as a string, otherwise None. """
    instructions = xmltree.find('instructions')
    if instructions is not None:
        instructions.tag = 'div'
        xmltree.remove(instructions)
        return etree.tostring(instructions, encoding='unicode')
    return None


def get_extension(srcurl):
    """get the extension of a given url """
    if 'youtu' in srcurl:
        return 'video/youtube'
    else:
        disassembled = urlparse(srcurl)
        file_ext = splitext(basename(disassembled.path))[1]
        return 'video/' + file_ext.replace('.', '')


class MLStripper(HTMLParser):
    "helper function for html_to_text below"
    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.fed = []

    def handle_data(self, data):
        """takes the data in separate chunks"""
        self.fed.append(data)

    def handle_entityref(self, name):
        """appends the reference to the body"""
        self.fed.append('&%s;' % name)

    def get_data(self):
        """joins together the seperate chunks into one cohesive string"""
        return ''.join(self.fed)


def html_to_text(html):
    "strips the html tags off of the text to return plaintext"
    htmlstripper = MLStripper()
    htmlstripper.feed(html)
    return htmlstripper.get_data()


class CommonAnnotatorMixin(object):
    annotation_storage_url = String(
        help=_("Location of Annotation backend"),
        scope=Scope.settings,
        default="http://your_annotation_storage.com",
        display_name=_("Url for Annotation Storage")
    )
    annotation_token_secret = String(
        help=_("Secret string for annotation storage"),
        scope=Scope.settings,
        default="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        display_name=_("Secret Token String for Annotation")
    )
    default_tab = String(
        display_name=_("Default Annotations Tab"),
        help=_("Select which tab will be the default in the annotations table: myNotes, Instructor, or Public."),
        scope=Scope.settings,
        default="myNotes",
    )
    # currently only supports one instructor, will build functionality for multiple later
    instructor_email = String(
        display_name=_("Email for 'Instructor' Annotations"),
        help=_("Email of the user that will be attached to all annotations that will be found in 'Instructor' tab."),
        scope=Scope.settings,
        default="",
    )
    annotation_mode = String(
        display_name=_("Mode for Annotation Tool"),
        help=_("Type in number corresponding to following modes:  'instructor' or 'everyone'"),
        scope=Scope.settings,
        default="everyone",
    )
