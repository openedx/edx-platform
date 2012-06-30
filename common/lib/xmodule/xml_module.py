from collections import MutableMapping
from xmodule.x_module import XModuleDescriptor
from lxml import etree


class LazyLoadingDict(MutableMapping):
    """
    A dictionary object that lazily loads it's contents from a provided
    function on reads (of members that haven't already been set)
    """

    def __init__(self, loader):
        self._contents = {}
        self._loaded = False
        self._loader = loader
        self._deleted = set()

    def __getitem__(self, name):
        if not (self._loaded or name in self._contents or name in self._deleted):
            self.load()

        return self._contents[name]

    def __setitem__(self, name, value):
        self._contents[name] = value
        self._deleted.discard(name)

    def __delitem__(self, name):
        del self._contents[name]
        self._deleted.add(name)

    def __contains__(self, name):
        self.load()
        return name in self._contents

    def __len__(self):
        self.load()
        return len(self._contents)

    def __iter__(self):
        self.load()
        return iter(self._contents)

    def load(self):
        if self._loaded:
            return

        loaded_contents = self._loader()
        loaded_contents.update(self._contents)
        self._contents = loaded_contents
        self._loaded = True


class XmlDescriptor(XModuleDescriptor):
    """
    Mixin class for standardized parsing of from xml
    """

    # Extension to append to filename paths
    filename_extension = 'xml'

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Return the definition to be passed to the newly created descriptor
        during from_xml

        xml_object: An etree Element
        """
        raise NotImplementedError("%s does not implement definition_from_xml" % cls.__name__)

    @classmethod
    def definition_from_file(cls, file, system):
        """
        Return the definition to be passed to the newly created descriptor
        during from_xml

        file: File pointer
        """
        return cls.definition_from_xml(etree.parse(file), system)

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses

        xml_data: A string of xml that will be translated into data and children for
            this module
        system: An XModuleSystem for interacting with external resources
        org and course are optional strings that will be used in the generated modules
            url identifiers
        """
        xml_object = etree.fromstring(xml_data)

        def metadata_loader():
            metadata = {}
            for attr in ('format', 'graceperiod', 'showanswer', 'rerandomize', 'due'):
                from_xml = xml_object.get(attr)
                if from_xml is not None:
                    metadata[attr] = from_xml

            if xml_object.get('graded') is not None:
                metadata['graded'] = xml_object.get('graded') == 'true'

            if xml_object.get('name') is not None:
                metadata['display_name'] = xml_object.get('name')

            return metadata

        def definition_loader():
            filename = xml_object.get('filename')
            if filename is None:
                return cls.definition_from_xml(xml_object, system)
            else:
                filepath = '{type}/{name}.{ext}'.format(type=xml_object.tag, name=filename, ext=cls.filename_extension)
                return cls.definition_from_file(system.resources_fs.open(filepath), system)

        return cls(
            system,
            LazyLoadingDict(definition_loader),
            location=['i4x',
                      org,
                      course,
                      xml_object.tag,
                      xml_object.get('slug')],
            metadata=LazyLoadingDict(metadata_loader),
        )

    def export_to_xml(self, resource_fs):
        """
        Returns an xml string representing this module, and all modules underneath it.
        May also write required resources out to resource_fs

        Assumes that modules have single parantage (that no module appears twice in the same course),
        and that it is thus safe to nest modules as xml children as appropriate.

        The returned XML should be able to be parsed back into an identical XModuleDescriptor
        using the from_xml method with the same system, org, and course
        """
        xml_object = self.definition_to_xml(resource_fs)
        xml_object.set('slug', self.name)
        xml_object.tag = self.type

        for attr in ('format', 'graceperiod', 'showanswer', 'rerandomize', 'due'):
            if attr in self.metadata and attr not in self._inherited_metadata:
                xml_object.set(attr, self.metadata[attr])

        if 'graded' in self.metadata and 'graded' not in self._inherited_metadata:
            xml_object.set('graded', str(self.metadata['graded']).lower())

        if 'display_name' in self.metadata:
            xml_object.set('name', self.metadata['display_name'])

        return etree.tostring(xml_object, pretty_print=True)

    def definition_to_xml(self, resource_fs):
        """
        Return a new etree Element object created from this modules definition.
        """
        raise NotImplementedError("%s does not implement definition_to_xml" % self.__class__.__name__)
