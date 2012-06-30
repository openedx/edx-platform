import logging
from fs.osfs import OSFS
from importlib import import_module
from lxml import etree
from path import path
from xmodule.x_module import XModuleDescriptor, XMLParsingSystem

from . import ModuleStore, Location
from .exceptions import ItemNotFoundError

etree.set_default_parser(etree.XMLParser(dtd_validation=False, load_dtd=False,
                                         remove_comments=True, remove_blank_text=True))

log = logging.getLogger(__name__)


class XMLModuleStore(ModuleStore):
    """
    An XML backed ModuleStore
    """
    def __init__(self, org, course, data_dir, default_class=None, eager=False):
        """
        Initialize an XMLModuleStore from data_dir

        org, course: Strings to be used in module keys
        data_dir: path to data directory containing course.xml
        default_class: dot-separated string defining the default descriptor class to use if non is specified in entry_points
        eager: If true, load the modules children immediately to force the entire course tree to be parsed
        """
        self.data_dir = path(data_dir)
        self.modules = {}

        module_path, _, class_name = default_class.rpartition('.')
        class_ = getattr(import_module(module_path), class_name)
        self.default_class = class_

        with open(self.data_dir / "course.xml") as course_file:
            class ImportSystem(XMLParsingSystem):
                def __init__(self, modulestore):
                    """
                    modulestore: the XMLModuleStore to store the loaded modules in
                    """
                    self.unnamed_modules = 0
                    self.used_slugs = set()

                    def process_xml(xml):
                        try:
                            xml_data = etree.fromstring(xml)
                        except:
                            log.exception("Unable to parse xml: {xml}".format(xml=xml))
                            raise
                        if xml_data.get('slug') is None:
                            if xml_data.get('name'):
                                slug = Location.clean(xml_data.get('name'))
                            else:
                                self.unnamed_modules += 1
                                slug = '{tag}_{count}'.format(tag=xml_data.tag, count=self.unnamed_modules)

                            if slug in self.used_slugs:
                                self.unnamed_modules += 1
                                slug = '{slug}_{count}'.format(slug=slug, count=self.unnamed_modules)

                            self.used_slugs.add(slug)
                            xml_data.set('slug', slug)

                        module = XModuleDescriptor.load_from_xml(etree.tostring(xml_data), self, org, course, modulestore.default_class)
                        modulestore.modules[module.location] = module

                        if eager:
                            module.get_children()
                        return module

                    XMLParsingSystem.__init__(self, modulestore.get_item, OSFS(data_dir), process_xml)

            ImportSystem(self).process_xml(course_file.read())

    def get_item(self, location):
        """
        Returns an XModuleDescriptor instance for the item at location.
        If location.revision is None, returns the most item with the most
        recent revision

        If any segment of the location is None except revision, raises
            keystore.exceptions.InsufficientSpecificationError
        If no object is found at that location, raises keystore.exceptions.ItemNotFoundError

        location: Something that can be passed to Location
        """
        location = Location(location)
        try:
            return self.modules[location]
        except KeyError:
            raise ItemNotFoundError(location)

    def create_item(self, location):
        raise NotImplementedError("XMLModuleStores are read-only")

    def update_item(self, location, data):
        """
        Set the data in the item specified by the location to
        data

        location: Something that can be passed to Location
        data: A nested dictionary of problem data
        """
        raise NotImplementedError("XMLModuleStores are read-only")

    def update_children(self, location, children):
        """
        Set the children for the item specified by the location to
        data

        location: Something that can be passed to Location
        children: A list of child item identifiers
        """
        raise NotImplementedError("XMLModuleStores are read-only")

    def update_metadata(self, location, metadata):
        """
        Set the metadata for the item specified by the location to
        metadata

        location: Something that can be passed to Location
        metadata: A nested dictionary of module metadata
        """
        raise NotImplementedError("XMLModuleStores are read-only")
