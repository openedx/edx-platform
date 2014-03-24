'''
Annotations Tool Mixin
This file contains global variables and functions used in the various Annotation Tools.
'''
from pkg_resources import resource_string
from lxml import etree
from urlparse import urlparse
from os.path import splitext, basename

def getInstructions(xmltree):
    """ Removes <instructions> from the xmltree and returns them as a string, otherwise None. """
    instructions = xmltree.find('instructions')
    if instructions is not None:
        instructions.tag = 'div'
        xmltree.remove(instructions)
        return etree.tostring(instructions, encoding='unicode')
    return None

def getExtension(srcurl):
    ''' get the extension of a given url '''
    if 'youtu' in srcurl:
        return 'video/youtube'
    else:
        disassembled = urlparse(srcurl)
        file_ext = splitext(basename(disassembled.path))[1]
        return 'video/' + file_ext.replace('.', '')

ANNOTATOR_COMMON_JS = [
    resource_string(__name__, 'js/src/ova/annotator-full.js'),
    resource_string(__name__, 'js/src/ova/video.dev.js'),
    resource_string(__name__, 'js/src/ova/rangeslider.js'),
    resource_string(__name__, 'js/src/ova/share-annotator.js'),
    resource_string(__name__, 'js/src/ova/tinymce.min.js'),
    resource_string(__name__, 'js/src/ova/richText-annotator.js'),
    resource_string(__name__, 'js/src/ova/reply-annotator.js'),
    resource_string(__name__, 'js/src/ova/tags-annotator.js'),
    resource_string(__name__, 'js/src/ova/flagging-annotator.js'),
    resource_string(__name__, 'js/src/ova/jquery-Watch.js'),
    resource_string(__name__, 'js/src/ova/diacritic-annotator.js'),
    resource_string(__name__, 'js/src/ova/ova.js'),
    resource_string(__name__, 'js/src/ova/catch/js/catch.js'),
    resource_string(__name__, 'js/src/ova/catch/js/handlebars-1.1.2.js'),
]

ANNOTATOR_COMMON_CSS = [
    resource_string(__name__, 'css/ova/edx-annotator.css'),
    resource_string(__name__, 'css/ova/annotator.css'),
    resource_string(__name__, 'css/ova/rangeslider.css'),
    resource_string(__name__, 'css/ova/share-annotator.css'),
    resource_string(__name__, 'css/ova/richText-annotator.css'),
    resource_string(__name__, 'css/ova/tags-annotator.css'),
    resource_string(__name__, 'css/ova/diacritic-annotator.css'),
    resource_string(__name__, 'css/ova/flagging-annotator.css'),
    resource_string(__name__, 'css/ova/ova.css'),
    resource_string(__name__, 'js/src/ova/catch/css/main.css'),
]