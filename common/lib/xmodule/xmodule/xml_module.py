from xmodule.x_module import (XModuleDescriptor, policy_key)
from xmodule.modulestore import Location
from lxml import etree
import json
import copy
import logging
import traceback
from collections import namedtuple
from fs.errors import ResourceNotFoundError
import os
import sys

log = logging.getLogger(__name__)

def name_to_pathname(name):
    """
    Convert a location name for use in a path: replace ':' with '/'.
    This allows users of the xml format to organize content into directories
    """
    return name.replace(':', '/')

def is_pointer_tag(xml_obj):
    """
    Check if xml_obj is a pointer tag: <blah url_name="something" />.
    No children, one attribute named url_name.

    Special case for course roots: the pointer is
      <course url_name="something" org="myorg"  course="course">

    xml_obj: an etree Element

    Returns a bool.
    """
    if xml_obj.tag != "course":
        expected_attr = set(['url_name'])
    else:
        expected_attr = set(['url_name', 'course', 'org'])

    actual_attr = set(xml_obj.attrib.keys())
    return len(xml_obj) == 0 and actual_attr == expected_attr

def get_metadata_from_xml(xml_object, remove=True):
    meta = xml_object.find('meta')
    if meta is None:
        return ''
    dmdata = meta.text
    #log.debug('meta for %s loaded: %s' % (xml_object,dmdata))
    if remove:
        xml_object.remove(meta)
    return dmdata

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

    # TODO (vshnayder): Do we need a list of metadata we actually
    # understand?  And if we do, is this the place?
    # Related: What's the right behavior for clean_metadata?
    metadata_attributes = ('format', 'graceperiod', 'showanswer', 'rerandomize',
        'start', 'due', 'graded', 'display_name', 'url_name', 'hide_from_toc',
        'ispublic', 	# if True, then course is listed for all users; see
        'xqa_key',	# for xqaa server access
        # VS[compat] Remove once unused.
        'name', 'slug')

    metadata_to_strip = ('data_dir',
           # VS[compat] -- remove the below attrs once everything is in the CMS
           'course', 'org', 'url_name', 'filename')

    # A dictionary mapping xml attribute names AttrMaps that describe how
    # to import and export them
    # Allow json to specify either the string "true", or the bool True.  The string is preferred.
    to_bool = lambda val: val == 'true' or val == True
    from_bool = lambda val: str(val).lower()
    bool_map = AttrMap(to_bool, from_bool)
    xml_attribute_map = {
        # type conversion: want True/False in python, "true"/"false" in xml
        'graded': bool_map,
        'hide_progress_tab': bool_map,
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

        # VS[compat] -- the filename attr should go away once everything is
        # converted.  (note: make sure html files still work once this goes away)
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
                    cls, 'backcompat_paths'):
                candidates = cls.backcompat_paths(filepath)
                for candidate in candidates:
                    if system.resources_fs.exists(candidate):
                        filepath = candidate
                        break

            definition_xml = cls.load_file(filepath, system.resources_fs, location)

        definition_metadata = get_metadata_from_xml(definition_xml)
        cls.clean_metadata_from_xml(definition_xml)
        definition = cls.definition_from_xml(definition_xml, system)
        if definition_metadata:
            definition['definition_metadata'] = definition_metadata

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
    def apply_policy(cls, metadata, policy):
        """
        Add the keys in policy to metadata, after processing them
        through the attrmap.  Updates the metadata dict in place.
        """
        for attr in policy:
            attr_map = cls.xml_attribute_map.get(attr, AttrMap())
            metadata[attr] = attr_map.from_xml(policy[attr])

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
        # VS[compat] -- just have the url_name lookup, once translation is done
        url_name = xml_object.get('url_name', xml_object.get('slug'))
        location = Location('i4x', org, course, xml_object.tag, url_name)

        # VS[compat] -- detect new-style each-in-a-file mode
        if is_pointer_tag(xml_object):
            # new style:
            # read the actual definition file--named using url_name.replace(':','/')
            filepath = cls._format_filepath(xml_object.tag, name_to_pathname(url_name))
            definition_xml = cls.load_file(filepath, system.resources_fs, location)
        else:
            definition_xml = xml_object	# this is just a pointer, not the real definition content

        definition = cls.load_definition(definition_xml, system, location)	# note this removes metadata
        # VS[compat] -- make Ike's github preview links work in both old and
        # new file layouts
        if is_pointer_tag(xml_object):
            # new style -- contents actually at filepath
            definition['filename'] = [filepath, filepath]

        metadata = cls.load_metadata(definition_xml)

        # move definition metadata into dict
        dmdata = definition.get('definition_metadata','')
        if dmdata:
            metadata['definition_metadata_raw'] = dmdata
            try:
                metadata.update(json.loads(dmdata))
            except Exception as err:
                log.debug('Error %s in loading metadata %s' % (err,dmdata))
                metadata['definition_metadata_err'] = str(err)

        # Set/override any metadata specified by policy
        k = policy_key(location)
        if k in system.policy:
            cls.apply_policy(metadata, system.policy[k])

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

    def export_to_file(self):
        """If this returns True, write the definition of this descriptor to a separate
        file.

        NOTE: Do not override this without a good reason.  It is here
        specifically for customtag...
        """
        return True


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
        for attr in sorted(self.own_metadata):
            # don't want e.g. data_dir
            if attr not in self.metadata_to_strip:
                xml_object.set(attr, val_for_xml(attr))

        if self.export_to_file():
            # Write the definition to a file
            url_path = name_to_pathname(self.url_name)
            filepath = self.__class__._format_filepath(self.category, url_path)
            resource_fs.makedir(os.path.dirname(filepath), allow_recreate=True)
            with resource_fs.open(filepath, 'w') as file:
                file.write(etree.tostring(xml_object, pretty_print=True))

            # And return just a pointer with the category and filename.
            record_object = etree.Element(self.category)
        else:
            record_object = xml_object

        record_object.set('url_name', self.url_name)

        # Special case for course pointers:
        if self.category == 'course':
            # add org and course attributes on the pointer tag
            record_object.set('org', self.location.org)
            record_object.set('course', self.location.course)

        return etree.tostring(record_object, pretty_print=True)

    def definition_to_xml(self, resource_fs):
        """
        Return a new etree Element object created from this modules definition.
        """
        raise NotImplementedError(
            "%s does not implement definition_to_xml" % self.__class__.__name__)
