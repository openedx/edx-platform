"""
Machinery to make the common case easy when building new runtimes
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from abc import ABCMeta, abstractmethod
from collections import namedtuple
import functools
import gettext
from io import BytesIO, StringIO
import itertools
import json
import logging
import re
import threading
import warnings

from lxml import etree
import markupsafe
import six

from web_fragments.fragment import Fragment

from xblock.core import XBlock, XBlockAside, XML_NAMESPACES
from xblock.fields import Field, BlockScope, Scope, ScopeIds, UserScope
from xblock.field_data import FieldData
from xblock.exceptions import (
    NoSuchViewError,
    NoSuchHandlerError,
    NoSuchServiceError,
    NoSuchUsage,
    NoSuchDefinition,
    FieldDataDeprecationWarning,
)


log = logging.getLogger(__name__)


class KeyValueStore(six.with_metaclass(ABCMeta, object)):
    """The abstract interface for Key Value Stores."""

    class Key(namedtuple("Key", "scope, user_id, block_scope_id, field_name, block_family")):
        """
        Keys are structured to retain information about the scope of the data.
        Stores can use this information however they like to store and retrieve
        data.
        """
        def __new__(cls, scope, user_id, block_scope_id, field_name, block_family='xblock.v1'):
            return super(KeyValueStore.Key, cls).__new__(cls, scope, user_id, block_scope_id, field_name, block_family)

    @abstractmethod
    def get(self, key):
        """Reads the value of the given `key` from storage."""
        pass

    @abstractmethod
    def set(self, key, value):
        """Sets `key` equal to `value` in storage."""
        pass

    @abstractmethod
    def delete(self, key):
        """Deletes `key` from storage."""
        pass

    @abstractmethod
    def has(self, key):
        """Returns whether or not `key` is present in storage."""
        pass

    def default(self, key):
        """
        Returns the context relevant default of the given `key`
        or raise KeyError which will result in the field's global default.
        """
        raise KeyError(repr(key))

    def set_many(self, update_dict):
        """
        For each (`key, value`) in `update_dict`, set `key` to `value` in storage.

        The default implementation brute force updates field by field through set which may be inefficient
        for any runtimes doing persistence operations on each set. Such implementations will want to
        override this method.

        :update_dict: field_name, field_value pairs for all cached changes
        """
        for key, value in six.iteritems(update_dict):
            self.set(key, value)


class DictKeyValueStore(KeyValueStore):
    """
    A `KeyValueStore` that stores everything into a Python dictionary.
    """
    def __init__(self, storage=None):
        self.db_dict = storage if storage is not None else {}

    def get(self, key):
        return self.db_dict[key]

    def set(self, key, value):
        self.db_dict[key] = value

    def set_many(self, other_dict):
        self.db_dict.update(other_dict)

    def delete(self, key):
        del self.db_dict[key]

    def has(self, key):
        return key in self.db_dict


class KvsFieldData(FieldData):
    """
    An interface mapping value access that uses field names to one
    that uses the correct scoped keys for the underlying KeyValueStore
    """

    def __init__(self, kvs, **kwargs):
        super(KvsFieldData, self).__init__(**kwargs)
        self._kvs = kvs

    def __repr__(self):
        return "{0.__class__.__name__}({0._kvs!r})".format(self)

    def _getfield(self, block, name):
        """
        Return the field with the given `name` from `block`.
        If no field with `name` exists in any namespace, raises a KeyError.

        :param block: xblock to retrieve the field from
        :type block: :class:`~xblock.core.XBlock`
        :param name: name of the field to retrieve
        :type name: str
        :raises KeyError: when no field with `name` exists in any namespace
        """

        # First, get the field from the class, if defined
        block_field = getattr(block.__class__, name, None)
        if block_field is not None and isinstance(block_field, Field):
            return block_field

        # Not in the class, so name
        # really doesn't name a field
        raise KeyError(name)

    def _key(self, block, name):
        """
        Resolves `name` to a key, in the following form:

        KeyValueStore.Key(
            scope=field.scope,
            user_id=student_id,
            block_scope_id=block_id,
            field_name=name,
            block_family=block.entry_point,
        )
        """
        field = self._getfield(block, name)
        if field.scope in (Scope.children, Scope.parent):
            block_id = block.scope_ids.usage_id
            user_id = None
        else:
            block_scope = field.scope.block

            if block_scope == BlockScope.ALL:
                block_id = None
            elif block_scope == BlockScope.USAGE:
                block_id = block.scope_ids.usage_id
            elif block_scope == BlockScope.DEFINITION:
                block_id = block.scope_ids.def_id
            elif block_scope == BlockScope.TYPE:
                block_id = block.scope_ids.block_type

            if field.scope.user == UserScope.ONE:
                user_id = block.scope_ids.user_id
            else:
                user_id = None

        key = KeyValueStore.Key(
            scope=field.scope,
            user_id=user_id,
            block_scope_id=block_id,
            field_name=name,
            block_family=block.entry_point,
        )
        return key

    def get(self, block, name):
        """
        Retrieve the value for the field named `name`.

        If a value is provided for `default`, then it will be
        returned if no value is set
        """
        return self._kvs.get(self._key(block, name))

    def set(self, block, name, value):
        """
        Set the value of the field named `name`
        """
        self._kvs.set(self._key(block, name), value)

    def delete(self, block, name):
        """
        Reset the value of the field named `name` to the default
        """
        self._kvs.delete(self._key(block, name))

    def has(self, block, name):
        """
        Return whether or not the field named `name` has a non-default value
        """
        try:
            return self._kvs.has(self._key(block, name))
        except KeyError:
            return False

    def set_many(self, block, update_dict):
        """Update the underlying model with the correct values."""
        updated_dict = {}

        # Generate a new dict with the correct mappings.
        for (key, value) in six.iteritems(update_dict):
            updated_dict[self._key(block, key)] = value

        self._kvs.set_many(updated_dict)

    def default(self, block, name):
        """
        Ask the kvs for the default (default implementation which other classes may override).

        :param block: block containing field to default
        :type block: :class:`~xblock.core.XBlock`
        :param name: name of the field to default
        """
        return self._kvs.default(self._key(block, name))


# The old name for KvsFieldData, to ease transition.
DbModel = KvsFieldData                                  # pylint: disable=C0103


class IdReader(six.with_metaclass(ABCMeta, object)):
    """An abstract object that stores usages and definitions."""

    @abstractmethod
    def get_usage_id_from_aside(self, aside_id):
        """
        Retrieve the XBlock `usage_id` associated with this aside usage id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `usage_id` of the usage the aside is commenting on.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_definition_id_from_aside(self, aside_id):
        """
        Retrieve the XBlock `definition_id` associated with this aside definition id.

        Args:
            aside_id: The definition id of the XBlockAside.

        Returns:
            The `definition_id` of the xblock the aside is commenting on.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_definition_id(self, usage_id):
        """Retrieve the definition that a usage is derived from.

        Args:
            usage_id: The id of the usage to query

        Returns:
            The `definition_id` the usage is derived from
        """
        raise NotImplementedError()

    @abstractmethod
    def get_block_type(self, def_id):
        """Retrieve the block_type of a particular definition

        Args:
            def_id: The id of the definition to query

        Returns:
            The `block_type` of the definition
        """
        raise NotImplementedError()

    @abstractmethod
    def get_aside_type_from_usage(self, aside_id):
        """
        Retrieve the XBlockAside `aside_type` associated with this aside
        usage id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `aside_type` of the aside.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_aside_type_from_definition(self, aside_id):
        """
        Retrieve the XBlockAside `aside_type` associated with this aside
        definition id.

        Args:
            aside_id: The definition id of the XBlockAside.

        Returns:
            The `aside_type` of the aside.
        """
        raise NotImplementedError()


class IdGenerator(six.with_metaclass(ABCMeta, object)):
    """An abstract object that creates usage and definition ids"""

    @abstractmethod
    def create_aside(self, definition_id, usage_id, aside_type):
        """
        Make a new aside definition and usage ids, indicating an :class:`.XBlockAside` of type `aside_type`
        commenting on an :class:`.XBlock` usage `usage_id`

        Returns:
            (aside_definition_id, aside_usage_id)
        """
        raise NotImplementedError()

    @abstractmethod
    def create_usage(self, def_id):
        """Make a usage, storing its definition id.

        Returns the newly-created usage id.
        """
        raise NotImplementedError()

    @abstractmethod
    def create_definition(self, block_type, slug=None):
        """Make a definition, storing its block type.

        If `slug` is provided, it is a suggestion that the definition id
        incorporate the slug somehow.

        Returns the newly-created definition id.

        """
        raise NotImplementedError()


class MemoryIdManager(IdReader, IdGenerator):
    """A simple dict-based implementation of IdReader and IdGenerator."""

    ASIDE_USAGE_ID = namedtuple('MemoryAsideUsageId', 'usage_id aside_type')
    ASIDE_DEFINITION_ID = namedtuple('MemoryAsideDefinitionId', 'definition_id aside_type')

    def __init__(self):
        self._ids = itertools.count()
        self._usages = {}
        self._definitions = {}

    def _next_id(self, prefix):
        """Generate a new id."""
        return "{}_{}".format(prefix, next(self._ids))

    def clear(self):
        """Remove all entries."""
        self._usages.clear()
        self._definitions.clear()

    def create_aside(self, definition_id, usage_id, aside_type):
        """Create the aside."""
        return (
            self.ASIDE_DEFINITION_ID(definition_id, aside_type),
            self.ASIDE_USAGE_ID(usage_id, aside_type),
        )

    def get_usage_id_from_aside(self, aside_id):
        """Extract the usage_id from the aside's usage_id."""
        return aside_id.usage_id

    def get_definition_id_from_aside(self, aside_id):
        """Extract the original xblock's definition_id from an aside's definition_id."""
        return aside_id.definition_id

    def create_usage(self, def_id):
        """Make a usage, storing its definition id."""
        usage_id = self._next_id("u")
        self._usages[usage_id] = def_id
        return usage_id

    def get_definition_id(self, usage_id):
        """Get a definition_id by its usage id."""
        try:
            return self._usages[usage_id]
        except KeyError:
            raise NoSuchUsage(repr(usage_id))

    def create_definition(self, block_type, slug=None):
        """Make a definition, storing its block type."""
        prefix = "d"
        if slug:
            prefix += "_" + slug
        def_id = self._next_id(prefix)
        self._definitions[def_id] = block_type
        return def_id

    def get_block_type(self, def_id):
        """Get a block_type by its definition id."""
        try:
            return self._definitions[def_id]
        except KeyError:
            try:
                return def_id.aside_type
            except AttributeError:
                raise NoSuchDefinition(repr(def_id))

    def get_aside_type_from_definition(self, aside_id):
        """Get an aside's type from its definition id."""
        return aside_id.aside_type

    def get_aside_type_from_usage(self, aside_id):
        """Get an aside's type from its usage id."""
        return aside_id.aside_type


class Runtime(six.with_metaclass(ABCMeta, object)):
    """
    Access to the runtime environment for XBlocks.
    """

    # Abstract methods
    @abstractmethod
    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        """Get the actual URL to invoke a handler.

        `handler_name` is the name of your handler function. Any additional
        portion of the url will be passed as the `suffix` argument to the handler.

        The return value is a complete absolute URL that will route through the
        runtime to your handler.

        :param block: The block to generate the url for
        :param handler_name: The handler on that block that the url should resolve to
        :param suffix: Any path suffix that should be added to the handler url
        :param query: Any query string that should be added to the handler url
            (which should not include an initial ? or &)
        :param thirdparty: If true, create a URL that can be used without the
            user being logged in.  This is useful for URLs to be used by third-party
            services.
        """
        raise NotImplementedError("Runtime needs to provide handler_url()")

    @abstractmethod
    def resource_url(self, resource):
        """Get the URL for a static resource file.

        `resource` is the application local path to the resource.

        The return value is a complete absolute URL that will locate the
        resource on your runtime.

        """
        raise NotImplementedError("Runtime needs to provide resource_url()")

    @abstractmethod
    def local_resource_url(self, block, uri):
        """Get the URL to load a static resource from an XBlock.

        `block` is the XBlock that owns the resource.

        `uri` is a relative URI to the resource. The XBlock class's
             get_local_resource(uri) method should be able to open the resource
             identified by this uri.

        Typically, this function uses `open_local_resource` defined on the
        XBlock class, which by default will only allow resources from the
        "public/" directory of the kit.  Resources must be placed in "public/"
        to be successfully served with this URL.

        The return value is a complete absolute URL which will locate the
        resource on your runtime.
        """
        raise NotImplementedError("Runtime needs to provide local_resource_url()")

    @abstractmethod
    def publish(self, block, event_type, event_data):
        """Publish an event.

        For example, to participate in the course grade, an XBlock should set
        has_score to True, and should publish a grade event whenever the grade
        changes.

        In this case the `event_type` would be `grade`, and the `event_data`
        would be a dictionary of the following form::

            {
                'value': <number>,
                'max_value': <number>,
            }

        The grade event represents a grade of value/max_value for the current
        user.

        `block` is the XBlock from which the event originates.
        """
        raise NotImplementedError("Runtime needs to provide publish()")

    # Construction
    def __init__(
            self, id_reader, field_data=None, mixins=(), services=None,
            default_class=None, select=None, id_generator=None
    ):
        """
        Arguments:
            id_reader (IdReader): An object that allows the `Runtime` to
                map between *usage_ids*, *definition_ids*, and *block_types*.

            id_generator (IdGenerator): The :class:`.IdGenerator` to use
                for creating ids when importing XML or loading XBlockAsides.

            field_data (FieldData): The :class:`.FieldData` to use by default when
                constructing an :class:`.XBlock` from this `Runtime`.

            mixins (tuple): Classes that should be mixed in with every :class:`.XBlock`
                created by this `Runtime`.

            services (dict): Services to make available through the
                :meth:`service` method.  There's no point passing anything here
                if you are overriding :meth:`service` in your sub-class.

            default_class (class): The default class to use if a class can't be found for a
                particular `block_type` when loading an :class:`.XBlock`.

            select: A function to select from one or more :class:`.XBlock` subtypes found
                when calling :meth:`.XBlock.load_class` to resolve a `block_type`.
                This is the same `select` as used by :meth:`.Plugin.load_class`.

        """
        self.id_reader = id_reader
        self._services = services or {}

        # Provide some default implementations
        self._services.setdefault("i18n", NullI18nService())

        self._deprecated_per_instance_field_data = field_data  # pylint: disable=invalid-name
        if field_data:
            warnings.warn(
                "Passing field_data as a constructor argument to Runtimes is deprecated",
                FieldDataDeprecationWarning,
                stacklevel=2
            )
            self._services.setdefault("field-data", field_data)

        self.default_class = default_class
        self.select = select

        self.user_id = None
        self.mixologist = Mixologist(mixins)
        self._view_name = None

        self.id_generator = id_generator
        if id_generator is None:
            warnings.warn("IdGenerator will be required in the future in order to support XBlockAsides", FutureWarning)

    # Block operations

    @property
    def field_data(self):
        """
        Access the FieldData passed in the constructor.

        Deprecated in favor of a 'field-data' service.
        """
        warnings.warn("Runtime.field_data is deprecated", FieldDataDeprecationWarning, stacklevel=2)
        return self._deprecated_per_instance_field_data

    @field_data.setter
    def field_data(self, field_data):
        """
        Set field_data.

        Deprecated in favor of a 'field-data' service.
        """
        warnings.warn("Runtime.field_data is deprecated", FieldDataDeprecationWarning, stacklevel=2)
        self._deprecated_per_instance_field_data = field_data

    def load_block_type(self, block_type):
        """
        Returns a subclass of :class:`.XBlock` that corresponds to the specified `block_type`.
        """
        return XBlock.load_class(block_type, self.default_class, self.select)

    def load_aside_type(self, aside_type):
        """
        Returns a subclass of :class:`.XBlockAside` that corresponds to the specified `aside_type`.
        """
        return XBlockAside.load_class(aside_type, select=self.select)

    def construct_xblock(self, block_type, scope_ids, field_data=None, *args, **kwargs):
        r"""
        Construct a new xblock of the type identified by block_type,
        passing \*args and \*\*kwargs into `__init__`.
        """
        return self.construct_xblock_from_class(
            cls=self.load_block_type(block_type),
            scope_ids=scope_ids,
            field_data=field_data,
            *args, **kwargs
        )

    def construct_xblock_from_class(self, cls, scope_ids, field_data=None, *args, **kwargs):
        """
        Construct a new xblock of type cls, mixing in the mixins
        defined for this application.
        """
        return self.mixologist.mix(cls)(
            runtime=self,
            field_data=field_data,
            scope_ids=scope_ids,
            *args, **kwargs
        )

    def get_block(self, usage_id, for_parent=None):
        """
        Create an XBlock instance in this runtime.

        The `usage_id` is used to find the XBlock class and data.
        """
        def_id = self.id_reader.get_definition_id(usage_id)
        try:
            block_type = self.id_reader.get_block_type(def_id)
        except NoSuchDefinition:
            raise NoSuchUsage(repr(usage_id))
        keys = ScopeIds(self.user_id, block_type, def_id, usage_id)
        block = self.construct_xblock(block_type, keys, for_parent=for_parent)
        return block

    def get_aside(self, aside_usage_id):
        """
        Create an XBlockAside in this runtime.

        The `aside_usage_id` is used to find the Aside class and data.
        """
        aside_type = self.id_reader.get_aside_type_from_usage(aside_usage_id)
        xblock_usage = self.id_reader.get_usage_id_from_aside(aside_usage_id)
        xblock_def = self.id_reader.get_definition_id(xblock_usage)
        aside_def_id, aside_usage_id = self.id_generator.create_aside(xblock_def, xblock_usage, aside_type)

        keys = ScopeIds(self.user_id, aside_type, aside_def_id, aside_usage_id)
        block = self.create_aside(aside_type, keys)
        return block

    # Parsing XML

    def parse_xml_string(self, xml, id_generator=None):
        """Parse a string of XML, returning a usage id."""
        if id_generator is not None:
            warnings.warn(
                "Passing an id_generator directly is deprecated "
                "in favor of constructing the Runtime with the id_generator",
                DeprecationWarning,
                stacklevel=2,
            )

        id_generator = id_generator or self.id_generator
        if isinstance(xml, six.binary_type):
            io_type = BytesIO
        else:
            io_type = StringIO
        return self.parse_xml_file(io_type(xml), id_generator)

    def parse_xml_file(self, fileobj, id_generator=None):
        """Parse an open XML file, returning a usage id."""
        root = etree.parse(fileobj).getroot()
        usage_id = self._usage_id_from_node(root, None, id_generator)
        return usage_id

    def _usage_id_from_node(self, node, parent_id, id_generator=None):
        """Create a new usage id from an XML dom node.

        Args:
            node (lxml.etree.Element): The DOM node to interpret.
            parent_id: The usage ID of the parent block
            id_generator (IdGenerator): The :class:`.IdGenerator` to use
                for creating ids
        """
        if id_generator is not None:
            warnings.warn(
                "Passing an id_generator directly is deprecated "
                "in favor of constructing the Runtime with the id_generator",
                DeprecationWarning,
                stacklevel=3,
            )

        id_generator = id_generator or self.id_generator

        block_type = node.tag
        # remove xblock-family from elements
        node.attrib.pop('xblock-family', None)
        # TODO: a way for this node to be a usage to an existing definition?
        def_id = id_generator.create_definition(block_type)
        usage_id = id_generator.create_usage(def_id)
        keys = ScopeIds(None, block_type, def_id, usage_id)
        block_class = self.mixologist.mix(self.load_block_type(block_type))
        # pull the asides out of the xml payload
        aside_children = []
        for child in node.iterchildren():
            # get xblock-family from node
            xblock_family = child.attrib.pop('xblock-family', None)
            if xblock_family:
                xblock_family = self._family_id_to_superclass(xblock_family)
                if issubclass(xblock_family, XBlockAside):
                    aside_children.append(child)
        # now process them & remove them from the xml payload
        for child in aside_children:
            self._aside_from_xml(child, def_id, usage_id, id_generator)
            node.remove(child)
        block = block_class.parse_xml(node, self, keys, id_generator)
        block.parent = parent_id
        block.save()
        return usage_id

    def _aside_from_xml(self, node, block_def_id, block_usage_id, id_generator):
        """
        Create an aside from the xml and attach it to the given block
        """
        id_generator = id_generator or self.id_generator

        aside_type = node.tag
        aside_class = self.load_aside_type(aside_type)
        aside_def_id, aside_usage_id = id_generator.create_aside(block_def_id, block_usage_id, aside_type)
        keys = ScopeIds(None, aside_type, aside_def_id, aside_usage_id)
        aside = aside_class.parse_xml(node, self, keys, id_generator)
        aside.save()

    def add_node_as_child(self, block, node, id_generator=None):
        """
        Called by XBlock.parse_xml to treat a child node as a child block.
        """
        usage_id = self._usage_id_from_node(node, block.scope_ids.usage_id, id_generator)
        block.children.append(usage_id)

    # Exporting XML

    def export_to_xml(self, block, xmlfile):
        """
        Export the block to XML, writing the XML to `xmlfile`.
        """
        root = etree.Element("unknown_root", nsmap=XML_NAMESPACES)
        tree = etree.ElementTree(root)
        block.add_xml_to_node(root)
        # write asides as children
        for aside in self.get_asides(block):
            if aside.needs_serialization():
                aside_node = etree.Element("unknown_root", nsmap=XML_NAMESPACES)
                aside.add_xml_to_node(aside_node)
                block.append(aside_node)
        tree.write(xmlfile, xml_declaration=True, pretty_print=True, encoding='utf-8')

    def add_block_as_child_node(self, block, node):
        """
        Export `block` as a child node of `node`.
        """
        child = etree.SubElement(node, "unknown")
        block.add_xml_to_node(child)

    # Rendering

    def render(self, block, view_name, context=None):
        """
        Render a block by invoking its view.

        Finds the view named `view_name` on `block`.  The default view will be
        used if a specific view hasn't be registered.  If there is no default
        view, an exception will be raised.

        The view is invoked, passing it `context`.  The value returned by the
        view is returned, with possible modifications by the runtime to
        integrate it into a larger whole.

        """
        # Set the active view so that :function:`render_child` can use it
        # as a default
        old_view_name = self._view_name
        self._view_name = view_name
        try:

            view_fn = getattr(block, view_name, None)
            if view_fn is None:
                view_fn = getattr(block, "fallback_view", None)
                if view_fn is None:
                    raise NoSuchViewError(block, view_name)
                view_fn = functools.partial(view_fn, view_name)

            frag = view_fn(context)

            # Explicitly save because render action may have changed state
            block.save()
            updated_frag = self.wrap_xblock(block, view_name, frag, context)
            return self.render_asides(block, view_name, updated_frag, context)
        finally:
            # Reset the active view to what it was before entering this method
            self._view_name = old_view_name

    def render_child(self, child, view_name=None, context=None):
        """A shortcut to render a child block.

        Use this method to render your children from your own view function.

        If `view_name` is not provided, it will default to the view name you're
        being rendered with.

        Returns the same value as :func:`render`.

        """
        return child.render(view_name or self._view_name, context)

    def render_children(self, block, view_name=None, context=None):
        """Render a block's children, returning a list of results.

        Each child of `block` will be rendered, just as :func:`render_child` does.

        Returns a list of values, each as provided by :func:`render`.

        """
        results = []
        for child_id in block.children:
            child = self.get_block(child_id)
            result = self.render_child(child, view_name, context)
            results.append(result)
        return results

    def wrap_xblock(self, block, view, frag, context):  # pylint: disable=W0613
        """
        Creates a div which identifies the xblock and writes out the json_init_args into a script tag.

        If there's a `wrap_child` method, it calls that with a deprecation warning.

        The default implementation creates a frag to wraps frag w/ a div identifying the xblock. If you have
        javascript, you'll need to override this impl
        """
        if hasattr(self, 'wrap_child'):
            log.warning("wrap_child is deprecated in favor of wrap_xblock and wrap_aside %s", self.__class__)
            return self.wrap_child(block, view, frag, context)  # pylint: disable=no-member

        extra_data = {'name': block.name} if block.name else {}
        return self._wrap_ele(block, view, frag, extra_data)

    def wrap_aside(self, block, aside, view, frag, context):  # pylint: disable=unused-argument
        """
        Creates a div which identifies the aside, points to the original block,
        and writes out the json_init_args into a script tag.

        The default implementation creates a frag to wraps frag w/ a div identifying the xblock. If you have
        javascript, you'll need to override this impl
        """
        return self._wrap_ele(
            aside, view, frag, {
                'block_id': block.scope_ids.usage_id,
                'url_selector': 'asideBaseUrl',
            })

    def _wrap_ele(self, block, view, frag, extra_data=None):
        """
        Does the guts of the wrapping the same way for both xblocks and asides. Their
        wrappers provide other info in extra_data which gets put into the dom data- attrs.
        """
        wrapped = Fragment()
        data = {
            'usage': block.scope_ids.usage_id,
            'block-type': block.scope_ids.block_type,
        }
        data.update(extra_data)

        if frag.js_init_fn:
            data['init'] = frag.js_init_fn
            data['runtime-version'] = frag.js_init_version

        json_init = ""
        # TODO/Note: We eventually want to remove: hasattr(frag, 'json_init_args')
        # However, I'd like to maintain backwards-compatibility with older XBlock
        # for at least a little while so as not to adversely effect developers.
        # pmitros/Jun 28, 2014.
        if hasattr(frag, 'json_init_args') and frag.json_init_args is not None:
            json_init = (
                '<script type="json/xblock-args" class="xblock_json_init_args">'
                '{data}</script>'
            ).format(data=json.dumps(frag.json_init_args))

        block_css_entrypoint = block.entry_point.replace('.', '-')
        css_classes = [
            block_css_entrypoint,
            '{}-{}'.format(block_css_entrypoint, view),
        ]

        html = "<div class='{}'{properties}>{body}{js}</div>".format(
            markupsafe.escape(' '.join(css_classes)),
            properties="".join(" data-%s='%s'" % item for item in list(data.items())),
            body=frag.body_html(),
            js=json_init)

        wrapped.add_content(html)
        wrapped.add_fragment_resources(frag)
        return wrapped

    # Asides

    def create_aside(self, block_type, keys):
        """
        The aside version of construct_xblock: take a type and key. Return an instance
        """
        aside_cls = XBlockAside.load_class(block_type)
        return aside_cls(runtime=self, scope_ids=keys)

    def get_asides(self, block):
        """
        Return instances for all of the asides that will decorate this `block`.

        Arguments:
            block (:class:`.XBlock`): The block to render retrieve asides for.

        Returns:
            List of XBlockAside instances
        """
        aside_instances = [
            self.get_aside_of_type(block, aside_type)
            for aside_type in self.applicable_aside_types(block)
        ]
        return [
            aside_instance for aside_instance in aside_instances
            if aside_instance.should_apply_to_block(block)
        ]

    # pylint: disable=unused-argument
    def applicable_aside_types(self, block):
        """
        Return the set of applicable aside types for this runtime and block. This method allows the runtime
        to filter the set of asides it wants to support or to provide even block-level or block_type level
        filtering. We may extend this in the future to also take the user or user roles.
        """
        return [aside_type for aside_type, __ in XBlockAside.load_classes()]

    def get_aside_of_type(self, block, aside_type):
        """
        Return the aside of the given aside_type which might be decorating this `block`.

        Arguments:
            block (:class:`.XBlock`): The block to retrieve asides for.
            aside_type (`str`): the type of the aside
        """
        # TODO: This function will need to be extended if we want to allow:
        #   a) XBlockAsides to statically indicated which types of blocks they can comment on
        #   b) XBlockRuntimes to limit the selection of asides to a subset of the installed asides
        #   c) Optimize by only loading asides that actually decorate a particular view

        if self.id_generator is None:
            raise Exception("Runtimes must be supplied with an IdGenerator to load XBlockAsides.")

        usage_id = block.scope_ids.usage_id

        aside_cls = self.load_aside_type(aside_type)
        definition_id = self.id_reader.get_definition_id(usage_id)
        aside_def_id, aside_usage_id = self.id_generator.create_aside(definition_id, usage_id, aside_type)
        scope_ids = ScopeIds(self.user_id, aside_type, aside_def_id, aside_usage_id)
        return aside_cls(runtime=self, scope_ids=scope_ids)

    def render_asides(self, block, view_name, frag, context):
        """
        Collect all of the asides' add ons and format them into the frag. The frag already
        has the given block's rendering.
        """
        aside_frag_fns = []
        for aside in self.get_asides(block):
            aside_view_fn = aside.aside_view_declaration(view_name)
            if aside_view_fn is not None:
                aside_frag_fns.append((aside, aside_view_fn))
        if aside_frag_fns:
            # layout (overideable by other runtimes)
            return self.layout_asides(block, context, frag, view_name, aside_frag_fns)
        return frag

    def layout_asides(self, block, context, frag, view_name, aside_frag_fns):
        """
        Execute and layout the aside_frags wrt the block's frag. Runtimes should feel free to override this
        method to control execution, place, and style the asides appropriately for their application

        This default method appends the aside_frags after frag. If you override this, you must
        call wrap_aside around each aside as per this function.

        Args:
            block (XBlock): the block being rendered
            frag (html): The result from rendering the block
            aside_frag_fns list((aside, aside_fn)): The asides and closures for rendering to call
        """
        result = Fragment(frag.content)
        result.add_fragment_resources(frag)

        for aside, aside_fn in aside_frag_fns:
            aside_frag = self.wrap_aside(block, aside, view_name, aside_fn(block, context), context)
            aside.save()
            result.add_content(aside_frag.content)
            result.add_fragment_resources(aside_frag)

        return result

    # Handlers

    def handle(self, block, handler_name, request, suffix=''):
        """
        Handles any calls to the specified `handler_name`.

        Provides a fallback handler if the specified handler isn't found.

        :param handler_name: The name of the handler to call
        :param request: The request to handle
        :type request: webob.Request
        :param suffix: The remainder of the url, after the handler url prefix, if available
        """
        handler = getattr(block, handler_name, None)
        if handler and getattr(handler, '_is_xblock_handler', False):
            # Cache results of the handler call for later saving
            results = handler(request, suffix)
        else:
            fallback_handler = getattr(block, "fallback_handler", None)
            if fallback_handler and getattr(fallback_handler, '_is_xblock_handler', False):
                # Cache results of the handler call for later saving
                results = fallback_handler(handler_name, request, suffix)
            else:
                raise NoSuchHandlerError("Couldn't find handler %r for %r" % (handler_name, block))

        # Write out dirty fields
        block.save()
        return results

    # Services

    def service(self, block, service_name):
        """Return a service, or None.

        Services are objects implementing arbitrary other interfaces.  They are
        requested by agreed-upon names, see [XXX TODO] for a list of possible
        services.  The object returned depends on the service requested.

        XBlocks must announce their intention to request services with the
        `XBlock.needs` or `XBlock.wants` decorators.  Use `needs` if you assume
        that the service is available, or `wants` if your code is flexible and
        can accept a None from this method.

        Runtimes can override this method if they have different techniques for
        finding and delivering services.

        Arguments:
            block (XBlock): this block's class will be examined for service
                decorators.
            service_name (str): the name of the service requested.

        Returns:
            An object implementing the requested service, or None.

        """
        declaration = block.service_declaration(service_name)
        if declaration is None:
            raise NoSuchServiceError("Service {!r} was not requested.".format(service_name))
        service = self._services.get(service_name)
        if service is None and declaration == "need":
            raise NoSuchServiceError("Service {!r} is not available.".format(service_name))
        return service

    # Querying

    def query(self, block):
        """Query for data in the tree, starting from `block`.

        Returns a Query object with methods for navigating the tree and
        retrieving information.

        """
        raise NotImplementedError("Querying is an experimental feature")

    def querypath(self, block, path):
        """An XPath-like interface to `query`."""
        class BadPath(Exception):
            """Bad path exception thrown when path cannot be found."""
            pass
        results = self.query(block)
        ROOT, SEP, WORD, FINAL = six.moves.range(4)               # pylint: disable=C0103
        state = ROOT
        lexer = RegexLexer(
            ("dotdot", r"\.\."),
            ("dot", r"\."),
            ("slashslash", r"//"),
            ("slash", r"/"),
            ("atword", r"@\w+"),
            ("word", r"\w+"),
            ("err", r"."),
        )
        for tokname, toktext in lexer.lex(path):
            if state == FINAL:
                # Shouldn't be any tokens after a last token.
                raise BadPath()
            if tokname == "dotdot":
                # .. (parent)
                if state == WORD:
                    raise BadPath()
                results = results.parent()
                state = WORD
            elif tokname == "dot":
                # . (current node)
                if state == WORD:
                    raise BadPath()
                state = WORD
            elif tokname == "slashslash":
                # // (descendants)
                if state == SEP:
                    raise BadPath()
                if state == ROOT:
                    raise NotImplementedError()
                results = results.descendants()
                state = SEP
            elif tokname == "slash":
                # / (here)
                if state == SEP:
                    raise BadPath()
                if state == ROOT:
                    raise NotImplementedError()
                state = SEP
            elif tokname == "atword":
                # @xxx (attribute access)
                if state != SEP:
                    raise BadPath()
                results = results.attr(toktext[1:])
                state = FINAL
            elif tokname == "word":
                # xxx (tag selection)
                if state != SEP:
                    raise BadPath()
                results = results.children().tagged(toktext)
                state = WORD
            else:
                raise BadPath("Invalid thing: %r" % toktext)
        return results

    def _family_id_to_superclass(self, family_id):
        """
        Temporary hardcoded mapping from serialized family id to either `class :XBlock:` or `:XBlockAside`
        """
        for family in [XBlock, XBlockAside]:
            if family_id == family.entry_point:
                return family
        raise ValueError('No such family: {}'.format(family_id))


class ObjectAggregator(object):
    """
    Provides a single object interface that combines many smaller objects.

    Attribute access on the aggregate object acts on the first sub-object
    that has that attribute.
    """

    def __init__(self, *objects):
        self.__dict__['_objects'] = objects

    def _object_with_attr(self, name):
        """
        Returns the first object that has the attribute `name`

        :param name: the attribute to filter by
        :type name: `str`
        :raises AttributeError: when no object has the named attribute
        """
        for obj in self._objects:
            if hasattr(obj, name):
                return obj

        raise AttributeError("No object has attribute {!r}".format(name))

    def __getattr__(self, name):
        return getattr(self._object_with_attr(name), name)

    def __setattr__(self, name, value):
        setattr(self._object_with_attr(name), name, value)

    def __delattr__(self, name):
        delattr(self._object_with_attr(name), name)


# Cache of Mixologist generated classes
_CLASS_CACHE = {}
_CLASS_CACHE_LOCK = threading.RLock()


class Mixologist(object):
    """
    Provides a facility to dynamically generate classes with additional mixins.
    """
    def __init__(self, mixins):
        """
        :param mixins: Classes to mixin
        :type mixins: `iterable` of `class`
        """
        self._mixins = tuple(mixins)

    def mix(self, cls):
        """
        Returns a subclass of `cls` mixed with `self.mixins`.

        :param cls: The base class to mix into
        :type cls: `class`
        """

        if hasattr(cls, 'unmixed_class'):
            base_class = cls.unmixed_class
            old_mixins = cls.__bases__[1:]  # Skip the original unmixed class
            mixins = old_mixins + tuple(
                mixin
                for mixin in self._mixins
                if mixin not in old_mixins
            )
        else:
            base_class = cls
            mixins = self._mixins

        mixin_key = (base_class, mixins)

        if mixin_key not in _CLASS_CACHE:
            # Only lock if we're about to make a new class
            with _CLASS_CACHE_LOCK:
                # Use setdefault so that if someone else has already
                # created a class before we got the lock, we don't
                # overwrite it
                return _CLASS_CACHE.setdefault(mixin_key, type(
                    base_class.__name__ + str('WithMixins'),  # type() requires native str
                    (base_class, ) + mixins,
                    {'unmixed_class': base_class}
                ))
        else:
            return _CLASS_CACHE[mixin_key]


class RegexLexer(object):
    """Split text into lexical tokens based on regexes."""
    def __init__(self, *toks):
        parts = []
        for name, regex in toks:
            parts.append("(?P<%s>%s)" % (name, regex))
        self.regex = re.compile("|".join(parts))

    def lex(self, text):
        """Iterator that tokenizes `text` and yields up tokens as they are found"""
        for match in self.regex.finditer(text):
            name = match.lastgroup
            yield (name, match.group(name))


class NullI18nService(object):
    """
    A simple implementation of the runtime "i18n" service.
    """
    def __init__(self):
        self._translations = gettext.NullTranslations()

    def __getattr__(self, name):
        return getattr(self._translations, name)

    STRFTIME_FORMATS = {
        "SHORT_DATE_FORMAT": "%b %d, %Y",
        "LONG_DATE_FORMAT": "%A, %B %d, %Y",
        "TIME_FORMAT": "%I:%M:%S %p",
        "DATE_TIME_FORMAT": "%b %d, %Y at %H:%M",
    }

    def strftime(self, dtime, format):      # pylint: disable=redefined-builtin
        """
        Locale-aware strftime, with format short-cuts.
        """
        format = self.STRFTIME_FORMATS.get(format + "_FORMAT", format)
        if six.PY2 and isinstance(format, six.text_type):
            format = format.encode("utf8")
        timestring = dtime.strftime(format)
        if six.PY2:
            timestring = timestring.decode("utf8")
        return timestring

    @property
    def ugettext(self):
        """
        Dispatch to the appropriate gettext method to handle text objects.

        Note that under python 3, this uses `gettext()`, while under python 2,
        it uses `ugettext()`.  This should not be used with bytestrings.
        """
        # pylint: disable=no-member
        if six.PY2:
            return self._translations.ugettext
        else:
            return self._translations.gettext

    @property
    def ungettext(self):
        """
        Dispatch to the appropriate ngettext method to handle text objects.

        Note that under python 3, this uses `ngettext()`, while under python 2,
        it uses `ungettext()`.  This should not be used with bytestrings.
        """
        # pylint: disable=no-member
        if six.PY2:
            return self._translations.ungettext
        else:
            return self._translations.ngettext
