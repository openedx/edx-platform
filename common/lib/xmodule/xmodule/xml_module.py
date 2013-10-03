import json
import copy
import logging
import os
import sys
from collections import namedtuple
from lxml import etree

from xblock.fields import Dict, Scope, ScopeIds
from xmodule.x_module import (XModuleDescriptor, policy_key)
from xmodule.modulestore import Location
from xmodule.modulestore.inheritance import own_metadata, InheritanceKeyValueStore
from xmodule.modulestore.xml_exporter import EdxJSONEncoder
from xblock.runtime import DbModel

log = logging.getLogger(__name__)

# assume all XML files are persisted as utf-8.
edx_xml_parser = etree.XMLParser(dtd_validation=False, load_dtd=False,
                                 remove_comments=True, remove_blank_text=True,
                                 encoding='utf-8')


def name_to_pathname(name):
    """
    Convert a location name for use in a path: replace ':' with '/'.
    This allows users of the xml format to organize content into directories
    """
    return name.replace(':', '/')


def is_pointer_tag(xml_obj):
    """
    Check if xml_obj is a pointer tag: <blah url_name="something" />.
    No children, one attribute named url_name, no text.

    Special case for course roots: the pointer is
      <course url_name="something" org="myorg" course="course">

    xml_obj: an etree Element

    Returns a bool.
    """
    if xml_obj.tag != "course":
        expected_attr = set(['url_name'])
    else:
        expected_attr = set(['url_name', 'course', 'org'])

    actual_attr = set(xml_obj.attrib.keys())

    has_text = xml_obj.text is not None and len(xml_obj.text.strip()) > 0

    return len(xml_obj) == 0 and actual_attr == expected_attr and not has_text


def get_metadata_from_xml(xml_object, remove=True):
    meta = xml_object.find('meta')
    if meta is None:
        return ''
    dmdata = meta.text
    if remove:
        xml_object.remove(meta)
    return dmdata


def serialize_field(value):
    """
    Return a string version of the value (where value is the JSON-formatted, internally stored value).

    If the value is a string, then we simply return what was passed in.
    Otherwise, we return json.dumps on the input value.
    """
    if isinstance(value, basestring):
        return value

    return json.dumps(value, cls=EdxJSONEncoder)


def deserialize_field(field, value):
    """
    Deserialize the string version to the value stored internally.

    Note that this is not the same as the value returned by from_json, as model types typically store
    their value internally as JSON. By default, this method will return the result of calling json.loads
    on the supplied value, unless json.loads throws a TypeError, or the type of the value returned by json.loads
    is not supported for this class (from_json throws an Error). In either of those cases, this method returns
    the input value.
    """
    try:
        deserialized = json.loads(value)
        if deserialized is None:
            return deserialized
        try:
            field.from_json(deserialized)
            return deserialized
        except (ValueError, TypeError):
            # Support older serialized version, which was just a string, not result of json.dumps.
            # If the deserialized version cannot be converted to the type (via from_json),
            # just return the original value. For example, if a string value of '3.4' was
            # stored for a String field (before we started storing the result of json.dumps),
            # then it would be deserialized as 3.4, but 3.4 is not supported for a String
            # field. Therefore field.from_json(3.4) will throw an Error, and we should
            # actually return the original value of '3.4'.
            return value

    except (ValueError, TypeError):
        # Support older serialized version.
        return value


class XmlDescriptor(XModuleDescriptor):
    """
    Mixin class for standardized parsing of from xml
    """

    xml_attributes = Dict(help="Map of unhandled xml attributes, used only for storage between import and export",
                          default={}, scope=Scope.settings)

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
                           'ispublic',  # if True, then course is listed for all users; see
                           'xqa_key',  # for xqaa server access
                           'giturl',  # url of git server for origin of file
                           # information about testcenter exams is a dict (of dicts), not a string,
                           # so it cannot be easily exportable as a course element's attribute.
                           'testcenter_info',
                           # VS[compat] Remove once unused.
                           'name', 'slug')

    metadata_to_strip = ('data_dir',
                         'tabs', 'grading_policy', 'published_by', 'published_date',
                         'discussion_blackouts', 'testcenter_info',
                         # VS[compat] -- remove the below attrs once everything is in the CMS
                         'course', 'org', 'url_name', 'filename',
                         # Used for storing xml attributes between import and export, for roundtrips
                         'xml_attributes')

    metadata_to_export_to_policy = ('discussion_topics', 'checklists')

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
        return etree.parse(file_object, parser=edx_xml_parser).getroot()

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
            if not system.resources_fs.exists(filepath) and hasattr(cls, 'backcompat_paths'):
                candidates = cls.backcompat_paths(filepath)
                for candidate in candidates:
                    if system.resources_fs.exists(candidate):
                        filepath = candidate
                        break

            definition_xml = cls.load_file(filepath, system.resources_fs, location)

        definition_metadata = get_metadata_from_xml(definition_xml)
        cls.clean_metadata_from_xml(definition_xml)
        definition, children = cls.definition_from_xml(definition_xml, system)
        if definition_metadata:
            definition['definition_metadata'] = definition_metadata
        definition['filename'] = [filepath, filename]

        return definition, children

    @classmethod
    def load_metadata(cls, xml_object):
        """
        Read the metadata attributes from this xml_object.

        Returns a dictionary {key: value}.
        """
        metadata = {'xml_attributes': {}}
        for attr, val in xml_object.attrib.iteritems():
            # VS[compat].  Remove after all key translations done
            attr = cls._translate(attr)

            if attr in cls.metadata_to_strip:
                # don't load these
                continue

            if attr not in cls.fields:
                metadata['xml_attributes'][attr] = val
            else:
                metadata[attr] = deserialize_field(cls.fields[attr], val)
        return metadata

    @classmethod
    def apply_policy(cls, metadata, policy):
        """
        Add the keys in policy to metadata, after processing them
        through the attrmap.  Updates the metadata dict in place.
        """
        for attr, value in policy.iteritems():
            attr = cls._translate(attr)
            if attr not in cls.fields:
                # Store unknown attributes coming from policy.json
                # in such a way that they will export to xml unchanged
                metadata['xml_attributes'][attr] = value
            else:
                metadata[attr] = value

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
            definition_xml = xml_object
            filepath = None

        definition, children = cls.load_definition(definition_xml, system, location)  # note this removes metadata

        # VS[compat] -- make Ike's github preview links work in both old and
        # new file layouts
        if is_pointer_tag(xml_object):
            # new style -- contents actually at filepath
            definition['filename'] = [filepath, filepath]

        metadata = cls.load_metadata(definition_xml)

        # move definition metadata into dict
        dmdata = definition.get('definition_metadata', '')
        if dmdata:
            metadata['definition_metadata_raw'] = dmdata
            try:
                metadata.update(json.loads(dmdata))
            except Exception as err:
                log.debug('Error %s in loading metadata %s' % (err, dmdata))
                metadata['definition_metadata_err'] = str(err)

        # Set/override any metadata specified by policy
        k = policy_key(location)
        if k in system.policy:
            cls.apply_policy(metadata, system.policy[k])

        field_data = {}
        field_data.update(metadata)
        field_data.update(definition)
        field_data['children'] = children

        field_data['xml_attributes']['filename'] = definition.get('filename', ['', None])  # for git link
        field_data['location'] = location
        field_data['category'] = xml_object.tag
        kvs = InheritanceKeyValueStore(initial_values=field_data)
        field_data = DbModel(kvs)

        return system.construct_xblock_from_class(
            cls,
            # We're loading a descriptor, so student_id is meaningless
            # We also don't have separate notions of definition and usage ids yet,
            # so we use the location for both
            ScopeIds(None, location.category, location, location),
            field_data,
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

        # Add the non-inherited metadata
        for attr in sorted(own_metadata(self)):
            # don't want e.g. data_dir
            if attr not in self.metadata_to_strip and attr not in self.metadata_to_export_to_policy:
                val = serialize_field(self._field_data.get(self, attr))
                try:
                    xml_object.set(attr, val)
                except Exception, e:
                    logging.exception('Failed to serialize metadata attribute {0} with value {1}. This could mean data loss!!!  Exception: {2}'.format(attr, val, e))
                    pass

        for key, value in self.xml_attributes.items():
            if key not in self.metadata_to_strip:
                xml_object.set(key, value)

        if self.export_to_file():
            # Write the definition to a file
            url_path = name_to_pathname(self.url_name)
            filepath = self.__class__._format_filepath(self.category, url_path)
            resource_fs.makedir(os.path.dirname(filepath), recursive=True, allow_recreate=True)
            with resource_fs.open(filepath, 'w') as file:
                file.write(etree.tostring(xml_object, pretty_print=True, encoding='utf-8'))

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

        return etree.tostring(record_object, pretty_print=True, encoding='utf-8')

    def definition_to_xml(self, resource_fs):
        """
        Return a new etree Element object created from this modules definition.
        """
        raise NotImplementedError(
            "%s does not implement definition_to_xml" % self.__class__.__name__)

    @property
    def non_editable_metadata_fields(self):
        non_editable_fields = super(XmlDescriptor, self).non_editable_metadata_fields
        non_editable_fields.append(XmlDescriptor.xml_attributes)
        return non_editable_fields
