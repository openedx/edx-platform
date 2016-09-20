"""
Factories for generating edXML for testing XModule import
"""

import inspect

from fs.memoryfs import MemoryFS
from factory import Factory, lazy_attribute, post_generation, Sequence
from lxml import etree

from xblock.mixins import HierarchyMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.x_module import XModuleMixin
from xmodule.modulestore import only_xmodules


class XmlImportData(object):
    """
    Class to capture all of the data needed to actually run an XML import,
    so that the Factories have something to generate
    """
    def __init__(self, xml_node, xml=None, course_id=None,
                 default_class=None, policy=None,
                 filesystem=None, parent=None,
                 xblock_mixins=(), xblock_select=None):

        self._xml_node = xml_node
        self._xml_string = xml
        self.course_id = course_id
        self.default_class = default_class
        self.filesystem = filesystem
        self.xblock_mixins = xblock_mixins
        self.xblock_select = xblock_select
        self.parent = parent

        if policy is None:
            self.policy = {}
        else:
            self.policy = policy

    @property
    def xml_string(self):
        """Return the stringified version of the generated xml"""
        if self._xml_string is not None:
            return self._xml_string

        return etree.tostring(self._xml_node)

    def __repr__(self):
        return u"XmlImportData{!r}".format((
            self._xml_node, self._xml_string, self.course_id,
            self.default_class, self.policy,
            self.filesystem, self.parent, self.xblock_mixins,
            self.xblock_select,
        ))


# Extract all argument names used to construct XmlImportData objects,
# so that the factory doesn't treat them as XML attributes
XML_IMPORT_ARGS = inspect.getargspec(XmlImportData.__init__).args


class XmlImportFactory(Factory):
    """
    Factory for generating XmlImportData's, which can hold all the data needed
    to run an XModule XML import
    """
    class Meta(object):
        model = XmlImportData

    filesystem = MemoryFS()
    xblock_mixins = (InheritanceMixin, XModuleMixin, HierarchyMixin)
    xblock_select = only_xmodules
    url_name = Sequence(str)
    attribs = {}
    policy = {}
    inline_xml = True
    tag = 'unknown'
    course_id = 'edX/xml_test_course/101'

    @classmethod
    def _adjust_kwargs(cls, **kwargs):
        """
        Adjust the kwargs to be passed to the generated class.

        Any kwargs that match :fun:`XmlImportData.__init__` will be passed
        through. Any other unknown `kwargs` will be treated as XML attributes

        :param tag: xml tag for the generated :class:`Element` node
        :param text: (Optional) specifies the text of the generated :class:`Element`.
        :param policy: (Optional) specifies data for the policy json file for this node
        :type policy: dict
        :param attribs: (Optional) specify attributes for the XML node
        :type attribs: dict
        """
        tag = kwargs.pop('tag', 'unknown')
        kwargs['policy'] = {'{tag}/{url_name}'.format(tag=tag, url_name=kwargs['url_name']): kwargs['policy']}

        kwargs['xml_node'].text = kwargs.pop('text', None)

        kwargs['xml_node'].attrib.update(kwargs.pop('attribs', {}))

        # Make sure that the xml_module doesn't try and open a file to find the contents
        # of this node.
        inline_xml = kwargs.pop('inline_xml')

        if inline_xml:
            kwargs['xml_node'].set('not_a_pointer', 'true')

        for key in kwargs.keys():
            if key not in XML_IMPORT_ARGS:
                kwargs['xml_node'].set(key, kwargs.pop(key))

        if not inline_xml:
            kwargs['xml_node'].write(
                kwargs['filesystem'].open(
                    '{}/{}.xml'.format(kwargs['tag'], kwargs['url_name'])
                ),
                encoding='utf-8'
            )

        return kwargs

    @lazy_attribute
    def xml_node(self):
        """An :class:`xml.etree.Element`"""
        return etree.Element(self.tag)

    @post_generation
    def parent(self, _create, extracted, **_):
        """Hook to merge this xml into a parent xml node"""
        if extracted is None:
            return

        extracted._xml_node.append(self._xml_node)  # pylint: disable=no-member, protected-access
        extracted.policy.update(self.policy)


class CourseFactory(XmlImportFactory):
    """Factory for <course> nodes"""
    tag = 'course'
    name = '101'
    static_asset_path = 'xml_test_course'


class ChapterFactory(XmlImportFactory):
    """Factory for <chapter> nodes"""
    tag = 'chapter'


class SequenceFactory(XmlImportFactory):
    """Factory for <sequential> nodes"""
    tag = 'sequential'


class VerticalFactory(XmlImportFactory):
    """Factory for <vertical> nodes"""
    tag = 'vertical'


class ProblemFactory(XmlImportFactory):
    """Factory for <problem> nodes"""
    tag = 'problem'
    text = '<h1>Empty Problem!</h1>'


class HtmlFactory(XmlImportFactory):
    """Factory for <html> nodes"""
    tag = 'html'
