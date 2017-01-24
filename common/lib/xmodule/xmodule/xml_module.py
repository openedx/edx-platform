import json
import copy
import logging
import os
import sys
from lxml import etree

from xblock.core import XML_NAMESPACES
from xblock.fields import Dict, Scope, ScopeIds
from xblock.runtime import KvsFieldData
from xmodule.x_module import XModuleDescriptor, DEPRECATION_VSCOMPAT_EVENT
from xmodule.modulestore.inheritance import own_metadata, InheritanceKeyValueStore
from xmodule.modulestore import EdxJSONEncoder

import dogstats_wrapper as dog_stats_api

from lxml.etree import (
    Element, ElementTree, XMLParser,
)

log = logging.getLogger(__name__)

# assume all XML files are persisted as utf-8.
EDX_XML_PARSER = XMLParser(dtd_validation=False, load_dtd=False,
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


class XmlParserMixin(object):
    """
    Class containing XML parsing functionality shared between XBlock and XModuleDescriptor.
    """
    # Extension to append to filename paths
    filename_extension = 'xml'

    xml_attributes = Dict(help="Map of unhandled xml attributes, used only for storage between import and export",
                          default={}, scope=Scope.settings)

    # VS[compat].  Backwards compatibility code that can go away after
    # importing 2012 courses.
    # A set of metadata key conversions that we want to make
    metadata_translations = {
        'slug': 'url_name',
        'name': 'display_name',
    }

    @classmethod
    def _translate(cls, key):
        """
        VS[compat]
        """
        return cls.metadata_translations.get(key, key)

    # The attributes will be removed from the definition xml passed
    # to definition_from_xml, and from the xml returned by definition_to_xml

    # Note -- url_name isn't in this list because it's handled specially on
    # import and export.

    metadata_to_strip = ('data_dir',
                         'tabs', 'grading_policy',
                         'discussion_blackouts',
                         # VS[compat] -- remove the below attrs once everything is in the CMS
                         'course', 'org', 'url_name', 'filename',
                         # Used for storing xml attributes between import and export, for roundtrips
                         'xml_attributes')

    metadata_to_export_to_policy = ('discussion_topics',)

    @staticmethod
    def _get_metadata_from_xml(xml_object, remove=True):
        """
        Extract the metadata from the XML.
        """
        meta = xml_object.find('meta')
        if meta is None:
            return ''
        dmdata = meta.text
        if remove:
            xml_object.remove(meta)
        return dmdata

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        """
        Return the definition to be passed to the newly created descriptor
        during from_xml

        xml_object: An etree Element
        """
        raise NotImplementedError("%s does not implement definition_from_xml" % cls.__name__)

    @classmethod
    def clean_metadata_from_xml(cls, xml_object):
        """
        Remove any attribute named for a field with scope Scope.settings from the supplied
        xml_object
        """
        for field_name, field in cls.fields.items():
            if field.scope == Scope.settings and xml_object.get(field_name) is not None:
                del xml_object.attrib[field_name]

    @classmethod
    def file_to_xml(cls, file_object):
        """
        Used when this module wants to parse a file object to xml
        that will be converted to the definition.

        Returns an lxml Element
        """
        return etree.parse(file_object, parser=EDX_XML_PARSER).getroot()

    @classmethod
    def load_file(cls, filepath, fs, def_id):  # pylint: disable=invalid-name
        """
        Open the specified file in fs, and call cls.file_to_xml on it,
        returning the lxml object.

        Add details and reraise on error.
        """
        try:
            with fs.open(filepath) as xml_file:
                return cls.file_to_xml(xml_file)
        except Exception as err:
            # Add info about where we are, but keep the traceback
            msg = 'Unable to load file contents at path %s for item %s: %s ' % (
                filepath, def_id, err)
            raise Exception, msg, sys.exc_info()[2]

    @classmethod
    def load_definition(cls, xml_object, system, def_id, id_generator):
        """
        Load a descriptor definition from the specified xml_object.
        Subclasses should not need to override this except in special
        cases (e.g. html module)

        Args:
            xml_object: an lxml.etree._Element containing the definition to load
            system: the modulestore system (aka, runtime) which accesses data and provides access to services
            def_id: the definition id for the block--used to compute the usage id and asides ids
            id_generator: used to generate the usage_id
        """

        # VS[compat] -- the filename attr should go away once everything is
        # converted.  (note: make sure html files still work once this goes away)
        filename = xml_object.get('filename')
        if filename is None:
            definition_xml = copy.deepcopy(xml_object)
            filepath = ''
            aside_children = []
        else:
            dog_stats_api.increment(
                DEPRECATION_VSCOMPAT_EVENT,
                tags=["location:xmlparser_util_mixin_load_definition_filename"]
            )

            filepath = cls._format_filepath(xml_object.tag, filename)

            # VS[compat]
            # TODO (cpennington): If the file doesn't exist at the right path,
            # give the class a chance to fix it up. The file will be written out
            # again in the correct format.  This should go away once the CMS is
            # online and has imported all current (fall 2012) courses from xml
            if not system.resources_fs.exists(filepath) and hasattr(cls, 'backcompat_paths'):
                dog_stats_api.increment(
                    DEPRECATION_VSCOMPAT_EVENT,
                    tags=["location:xmlparser_util_mixin_load_definition_backcompat"]
                )

                candidates = cls.backcompat_paths(filepath)
                for candidate in candidates:
                    if system.resources_fs.exists(candidate):
                        filepath = candidate
                        break

            definition_xml = cls.load_file(filepath, system.resources_fs, def_id)
            usage_id = id_generator.create_usage(def_id)
            aside_children = system.parse_asides(definition_xml, def_id, usage_id, id_generator)

            # Add the attributes from the pointer node
            definition_xml.attrib.update(xml_object.attrib)

        definition_metadata = cls._get_metadata_from_xml(definition_xml)
        cls.clean_metadata_from_xml(definition_xml)
        definition, children = cls.definition_from_xml(definition_xml, system)
        if definition_metadata:
            definition['definition_metadata'] = definition_metadata
        definition['filename'] = [filepath, filename]

        if aside_children:
            definition['aside_children'] = aside_children

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
                if attr in ('course', 'org', 'url_name', 'filename'):
                    dog_stats_api.increment(
                        DEPRECATION_VSCOMPAT_EVENT,
                        tags=(
                            "location:xmlparser_util_mixin_load_metadata",
                            "metadata:{}".format(attr),
                        )
                    )
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
    def parse_xml(cls, node, runtime, keys, id_generator):  # pylint: disable=unused-argument
        """
        Use `node` to construct a new block.

        Arguments:
            node (etree.Element): The xml node to parse into an xblock.

            runtime (:class:`.Runtime`): The runtime to use while parsing.

            keys (:class:`.ScopeIds`): The keys identifying where this block
                will store its data.

            id_generator (:class:`.IdGenerator`): An object that will allow the
                runtime to generate correct definition and usage ids for
                children of this block.

        Returns (XBlock): The newly parsed XBlock

        """
        # VS[compat] -- just have the url_name lookup, once translation is done
        url_name = cls._get_url_name(node)
        def_id = id_generator.create_definition(node.tag, url_name)
        usage_id = id_generator.create_usage(def_id)
        aside_children = []

        # VS[compat] -- detect new-style each-in-a-file mode
        if is_pointer_tag(node):
            # new style:
            # read the actual definition file--named using url_name.replace(':','/')
            definition_xml, filepath = cls.load_definition_xml(node, runtime, def_id)
            aside_children = runtime.parse_asides(definition_xml, def_id, usage_id, id_generator)
        else:
            filepath = None
            definition_xml = node
            dog_stats_api.increment(
                DEPRECATION_VSCOMPAT_EVENT,
                tags=["location:xmlparser_util_mixin_parse_xml"]
            )

        # Note: removes metadata.
        definition, children = cls.load_definition(definition_xml, runtime, def_id, id_generator)

        # VS[compat] -- make Ike's github preview links work in both old and
        # new file layouts
        if is_pointer_tag(node):
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
                log.debug('Error in loading metadata %r', dmdata, exc_info=True)
                metadata['definition_metadata_err'] = str(err)

        definition_aside_children = definition.pop('aside_children', None)
        if definition_aside_children:
            aside_children.extend(definition_aside_children)

        # Set/override any metadata specified by policy
        cls.apply_policy(metadata, runtime.get_policy(usage_id))

        field_data = {}
        field_data.update(metadata)
        field_data.update(definition)
        field_data['children'] = children

        field_data['xml_attributes']['filename'] = definition.get('filename', ['', None])  # for git link
        kvs = InheritanceKeyValueStore(initial_values=field_data)
        field_data = KvsFieldData(kvs)

        xblock = runtime.construct_xblock_from_class(
            cls,
            # We're loading a descriptor, so student_id is meaningless
            ScopeIds(None, node.tag, def_id, usage_id),
            field_data,
        )

        if aside_children:
            asides_tags = [x.tag for x in aside_children]
            asides = runtime.get_asides(xblock)
            for asd in asides:
                if asd.scope_ids.block_type in asides_tags:
                    xblock.add_aside(asd)

        return xblock

    @classmethod
    def _get_url_name(cls, node):
        """
        Reads url_name attribute from the node
        """
        return node.get('url_name', node.get('slug'))

    @classmethod
    def load_definition_xml(cls, node, runtime, def_id):
        """
        Loads definition_xml stored in a dedicated file
        """
        url_name = cls._get_url_name(node)
        filepath = cls._format_filepath(node.tag, name_to_pathname(url_name))
        definition_xml = cls.load_file(filepath, runtime.resources_fs, def_id)
        return definition_xml, filepath

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

    def add_xml_to_node(self, node):
        """
        For exporting, set data on `node` from ourselves.
        """
        # Get the definition
        xml_object = self.definition_to_xml(self.runtime.export_fs)
        for aside in self.runtime.get_asides(self):
            if aside.needs_serialization():
                aside_node = etree.Element("unknown_root", nsmap=XML_NAMESPACES)
                aside.add_xml_to_node(aside_node)
                xml_object.append(aside_node)

        self.clean_metadata_from_xml(xml_object)

        # Set the tag on both nodes so we get the file path right.
        xml_object.tag = self.category
        node.tag = self.category

        # Add the non-inherited metadata
        for attr in sorted(own_metadata(self)):
            # don't want e.g. data_dir
            if attr not in self.metadata_to_strip and attr not in self.metadata_to_export_to_policy:
                val = serialize_field(self._field_data.get(self, attr))
                try:
                    xml_object.set(attr, val)
                except Exception:
                    logging.exception(
                        u'Failed to serialize metadata attribute %s with value %s in module %s. This could mean data loss!!!',
                        attr, val, self.url_name
                    )

        for key, value in self.xml_attributes.items():
            if key not in self.metadata_to_strip:
                xml_object.set(key, serialize_field(value))

        if self.export_to_file():
            # Write the definition to a file
            url_path = name_to_pathname(self.url_name)
            filepath = self._format_filepath(self.category, url_path)
            self.runtime.export_fs.makedir(os.path.dirname(filepath), recursive=True, allow_recreate=True)
            with self.runtime.export_fs.open(filepath, 'w') as fileobj:
                ElementTree(xml_object).write(fileobj, pretty_print=True, encoding='utf-8')
        else:
            # Write all attributes from xml_object onto node
            node.clear()
            node.tag = xml_object.tag
            node.text = xml_object.text
            node.tail = xml_object.tail
            node.attrib.update(xml_object.attrib)
            node.extend(xml_object)

        node.set('url_name', self.url_name)

        # Special case for course pointers:
        if self.category == 'course':
            # add org and course attributes on the pointer tag
            node.set('org', self.location.org)
            node.set('course', self.location.course)

    def definition_to_xml(self, resource_fs):
        """
        Return a new etree Element object created from this modules definition.
        """
        raise NotImplementedError(
            "%s does not implement definition_to_xml" % self.__class__.__name__)

    @property
    def non_editable_metadata_fields(self):
        """
        Return a list of all metadata fields that cannot be edited.
        """
        non_editable_fields = super(XmlParserMixin, self).non_editable_metadata_fields
        non_editable_fields.append(XmlParserMixin.xml_attributes)
        return non_editable_fields


class XmlDescriptor(XmlParserMixin, XModuleDescriptor):  # pylint: disable=abstract-method
    """
    Mixin class for standardized parsing of XModule xml.
    """
    resources_dir = None

    @classmethod
    def from_xml(cls, xml_data, system, id_generator):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses.

        Args:
            xml_data (str): A string of xml that will be translated into data and children
                for this module

            system (:class:`.XMLParsingSystem):

            id_generator (:class:`xblock.runtime.IdGenerator`): Used to generate the
                usage_ids and definition_ids when loading this xml

        """
        # Shim from from_xml to the parse_xml defined in XmlParserMixin.
        # This only exists to satisfy subclasses that both:
        #    a) define from_xml themselves
        #    b) call super(..).from_xml(..)
        return super(XmlDescriptor, cls).parse_xml(
            etree.fromstring(xml_data),
            system,
            None,  # This is ignored by XmlParserMixin
            id_generator,
        )

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Interpret the parsed XML in `node`, creating an XModuleDescriptor.
        """
        if cls.from_xml != XmlDescriptor.from_xml:
            # Skip the parse_xml from XmlParserMixin to get the shim parse_xml
            # from XModuleDescriptor, which actually calls `from_xml`.
            return super(XmlParserMixin, cls).parse_xml(node, runtime, keys, id_generator)  # pylint: disable=bad-super-call
        else:
            return super(XmlDescriptor, cls).parse_xml(node, runtime, keys, id_generator)

    def export_to_xml(self, resource_fs):
        """
        Returns an xml string representing this module, and all modules
        underneath it.  May also write required resources out to resource_fs.

        Assumes that modules have single parentage (that no module appears twice
        in the same course), and that it is thus safe to nest modules as xml
        children as appropriate.

        The returned XML should be able to be parsed back into an identical
        XModuleDescriptor using the from_xml method with the same system, org,
        and course
        """
        # Shim from export_to_xml to the add_xml_to_node defined in XmlParserMixin.
        # This only exists to satisfy subclasses that both:
        #    a) define export_to_xml themselves
        #    b) call super(..).export_to_xml(..)
        node = Element(self.category)
        super(XmlDescriptor, self).add_xml_to_node(node)
        return etree.tostring(node)

    def add_xml_to_node(self, node):
        """
        Export this :class:`XModuleDescriptor` as XML, by setting attributes on the provided
        `node`.
        """
        if self.export_to_xml != XmlDescriptor.export_to_xml:
            # Skip the add_xml_to_node from XmlParserMixin to get the shim add_xml_to_node
            # from XModuleDescriptor, which actually calls `export_to_xml`.
            super(XmlParserMixin, self).add_xml_to_node(node)  # pylint: disable=bad-super-call
        else:
            super(XmlDescriptor, self).add_xml_to_node(node)
