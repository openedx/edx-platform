from xmodule.x_module import XModuleDescriptor
from xmodule.modulestore import Location
from lxml import etree
import copy
import logging
import traceback
from collections import namedtuple
from fs.errors import ResourceNotFoundError
import os
import sys

log = logging.getLogger(__name__)

_AttrMapBase = namedtuple('_AttrMap', 'from_xml to_xml')

class AttrMap(_AttrMapBase):
    """
    A class that specifies two functions:

        from_xml: convert value from the xml representation into
            an internal python representation

        to_xml: convert the internal python representation into
            the value to store in the xml.
    """
    def __new__(_cls, from_xml=lambda x: x,
                to_xml=lambda x: x):
        return _AttrMapBase.__new__(_cls, from_xml, to_xml)


class XmlDescriptor(XModuleDescriptor):
    """
    Mixin class for standardized parsing of from xml
    """

    # Extension to append to filename paths
    filename_extension = 'xml'

    # The attributes will be removed from the definition xml passed
    # to definition_from_xml, and from the xml returned by definition_to_xml

    # Note -- url_name isn't in this list because it's handled specially on
    # import and export.
    metadata_attributes = ('format', 'graceperiod', 'showanswer', 'rerandomize',
        'start', 'due', 'graded', 'display_name', 'url_name', 'hide_from_toc',
        'ispublic', 	# if True, then course is listed for all users; see 
        # VS[compat] Remove once unused.
        'name', 'slug')

    # VS[compat] -- remove once everything is in the CMS
    # We don't want url_name in the metadata--it's in the location, so avoid
    # confusion and duplication.
    metadata_to_strip = ('url_name', )

    # A dictionary mapping xml attribute names AttrMaps that describe how
    # to import and export them
    xml_attribute_map = {
        # type conversion: want True/False in python, "true"/"false" in xml
        'graded': AttrMap(lambda val: val == 'true',
                          lambda val: str(val).lower()),
    }


    # VS[compat].  Backwards compatibility code that can go away after
    # importing 2012 courses.
    # A set of metadata key conversions that we want to make
    metadata_translations = {
        'slug' : 'url_name',
        'name' : 'display_name',
        }

    @classmethod
    def _translate(cls, key):
        'VS[compat]'
        return cls.metadata_translations.get(key, key)


    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Return the definition to be passed to the newly created descriptor
        during from_xml

        xml_object: An etree Element
        """
        raise NotImplementedError(
            "%s does not implement definition_from_xml" % cls.__name__)

    @classmethod
    def clean_metadata_from_xml(cls, xml_object):
        """
        Remove any attribute named in cls.metadata_attributes from the supplied
        xml_object
        """
        for attr in cls.metadata_attributes:
            if xml_object.get(attr) is not None:
                del xml_object.attrib[attr]

    @classmethod
    def file_to_xml(cls, file_object):
        """
        Used when this module wants to parse a file object to xml
        that will be converted to the definition.

        Returns an lxml Element
        """
        return etree.parse(file_object).getroot()

    @classmethod
    def load_file(cls, filepath, fs, location):
        '''
        Open the specified file in fs, and call cls.file_to_xml on it,
        returning the lxml object.

        Add details and reraise on error.
        '''
        try:
            with fs.open(filepath) as file:
                return cls.file_to_xml(file)
        except Exception as err:
            # Add info about where we are, but keep the traceback
            msg = 'Unable to load file contents at path %s for item %s: %s ' % (
                filepath, location.url(), str(err))
            raise Exception, msg, sys.exc_info()[2]


    @classmethod
    def load_definition(cls, xml_object, system, location):
        '''Load a descriptor definition from the specified xml_object.
        Subclasses should not need to override this except in special
        cases (e.g. html module)'''

        filename = xml_object.get('filename')
        if filename is None:
            definition_xml = copy.deepcopy(xml_object)
            filepath = ''
        else:
            filepath = cls._format_filepath(xml_object.tag, filename)

            # VS[compat]
            # TODO (cpennington): If the file doesn't exist at the right path,
            # give the class a chance to fix it up. The file will be written out
            # again in the correct format.  This should go away once the CMS is
            # online and has imported all current (fall 2012) courses from xml
            if not system.resources_fs.exists(filepath) and hasattr(
                    cls,
                    'backcompat_paths'):
                candidates = cls.backcompat_paths(filepath)
                for candidate in candidates:
                    if system.resources_fs.exists(candidate):
                        filepath = candidate
                        break

            definition_xml = cls.load_file(filepath, system.resources_fs, location)

        cls.clean_metadata_from_xml(definition_xml)
        definition = cls.definition_from_xml(definition_xml, system)

        # TODO (ichuang): remove this after migration
        # for Fall 2012 LMS migration: keep filename (and unmangled filename)
        definition['filename'] = [ filepath, filename ]

        return definition

    @classmethod
    def load_metadata(cls, xml_object):
        """
        Read the metadata attributes from this xml_object.

        Returns a dictionary {key: value}.
        """
        metadata = {}
        for attr in xml_object.attrib:
            val = xml_object.get(attr)
            if val is not None:
                # VS[compat].  Remove after all key translations done
                attr = cls._translate(attr)

                if attr in cls.metadata_to_strip:
                    # don't load these
                    continue

                attr_map = cls.xml_attribute_map.get(attr, AttrMap())
                metadata[attr] = attr_map.from_xml(val)
        return metadata


    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses

        xml_data: A string of xml that will be translated into data and children for
            this module
        system: A DescriptorSystem for interacting with external resources
        org and course are optional strings that will be used in the generated modules
            url identifiers
        """
        xml_object = etree.fromstring(xml_data)
        # VS[compat] -- just have the url_name lookup once translation is done
        url_name = xml_object.get('url_name', xml_object.get('slug'))
        location = Location('i4x', org, course, xml_object.tag, url_name)

        # VS[compat] -- detect new-style each-in-a-file mode
        if len(xml_object.attrib.keys()) == 1 and len(xml_object) == 0:
            # new style: this is just a pointer.
            # read the actual defition file--named using url_name
            filepath = cls._format_filepath(xml_object.tag, url_name)
            definition_xml = cls.load_file(filepath, system.resources_fs, location)
        else:
            definition_xml = xml_object

        definition = cls.load_definition(definition_xml, system, location)
        metadata = cls.load_metadata(definition_xml)
        return cls(
            system,
            definition,
            location=location,
            metadata=metadata,
        )

    @classmethod
    def _format_filepath(cls, category, name):
        return u'{category}/{name}.{ext}'.format(category=category,
                                                 name=name,
                                                 ext=cls.filename_extension)

    def export_to_xml(self, resource_fs):
        """
        Returns an xml string representing this module, and all modules
        underneath it.  May also write required resources out to resource_fs

        Assumes that modules have single parentage (that no module appears twice
        in the same course), and that it is thus safe to nest modules as xml
        children as appropriate.

        The returned XML should be able to be parsed back into an identical
        XModuleDescriptor using the from_xml method with the same system, org,
        and course

        resource_fs is a pyfilesystem object (from the fs package)
        """

        # Get the definition
        xml_object = self.definition_to_xml(resource_fs)
        self.__class__.clean_metadata_from_xml(xml_object)

        # Set the tag so we get the file path right
        xml_object.tag = self.category

        def val_for_xml(attr):
            """Get the value for this attribute that we want to store.
            (Possible format conversion through an AttrMap).
             """
            attr_map = self.xml_attribute_map.get(attr, AttrMap())
            return attr_map.to_xml(self.own_metadata[attr])

        # Add the non-inherited metadata
        for attr in self.own_metadata:
            xml_object.set(attr, val_for_xml(attr))

        # Write the actual contents to a file
        filepath = self.__class__._format_filepath(self.category, self.url_name)
        resource_fs.makedir(os.path.dirname(filepath), allow_recreate=True)

        with resource_fs.open(filepath, 'w') as file:
            file.write(etree.tostring(xml_object, pretty_print=True))

        # And return just a pointer with the category and filename.
        record_object = etree.Element(self.category)
        record_object.set('url_name', self.url_name)

        return etree.tostring(record_object, pretty_print=True)

    def definition_to_xml(self, resource_fs):
        """
        Return a new etree Element object created from this modules definition.
        """
        raise NotImplementedError(
            "%s does not implement definition_to_xml" % self.__class__.__name__)
