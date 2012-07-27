import logging
import os
from lxml import etree

from xmodule.x_module import XModule
from xmodule.raw_module import RawDescriptor

log = logging.getLogger("mitx.courseware")


class HtmlModule(XModule):
    def get_html(self):
        return self.html

    def __init__(self, system, location, definition,
                 instance_state=None, shared_state=None, **kwargs):
        XModule.__init__(self, system, location, definition,
                         instance_state, shared_state, **kwargs)
        self.html = self.definition['data']


class HtmlDescriptor(RawDescriptor):
    """
    Module for putting raw html in a course
    """
    mako_template = "widgets/html-edit.html"
    module_class = HtmlModule
    filename_extension = "html"

    # TODO (cpennington): Delete this method once all fall 2012 course are being
    # edited in the cms
    @classmethod
    def backcompat_paths(cls, path):
        if path.endswith('.html.html'):
            path = path[:-5]
        candidates = []
        while os.sep in path:
            candidates.append(path)
            _, _, path = path.partition(os.sep)

        return candidates

    @classmethod
    def file_to_xml(cls, file_object):
        parser = etree.HTMLParser()
        return etree.parse(file_object, parser).getroot()

    @classmethod
    def split_to_file(cls, xml_object):
        # never include inline html
        return True
