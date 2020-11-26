"""
Annotations Tool Mixin
This file contains global variables and functions used in the various Annotation Tools.
"""


from os.path import basename, splitext

from lxml import etree
from six.moves.html_parser import HTMLParser
from six.moves.urllib.parse import urlparse


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
