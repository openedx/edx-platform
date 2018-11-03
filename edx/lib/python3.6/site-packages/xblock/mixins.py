"""
This module defines all of the Mixins that provide components of XBlock-family
functionality, such as ScopeStorage, RuntimeServices, and Handlers.
"""

from __future__ import absolute_import, division, print_function, unicode_literals


from collections import OrderedDict
import copy
import functools
import inspect
import logging
import warnings
import json

from lxml import etree
import six
from webob import Response

from xblock.exceptions import JsonHandlerError, KeyValueMultiSaveError, XBlockSaveError, FieldDataDeprecationWarning
from xblock.fields import Field, Reference, Scope, ReferenceList
from xblock.internal import class_lazy, NamedAttributesMetaclass


# OrderedDict is used so that namespace attributes are put in predictable order
# This allows for simple string equality assertions in tests and have no other effects
XML_NAMESPACES = OrderedDict([
    ("option", "http://code.edx.org/xblock/option"),
    ("block", "http://code.edx.org/xblock/block"),
])


class HandlersMixin(object):
    """
    A mixin provides all of the machinery needed for working with XBlock-style handlers.
    """

    @classmethod
    def json_handler(cls, func):
        """
        Wrap a handler to consume and produce JSON.

        Rather than a Request object, the method will now be passed the
        JSON-decoded body of the request. The request should be a POST request
        in order to use this method. Any data returned by the function
        will be JSON-encoded and returned as the response.

        The wrapped function can raise JsonHandlerError to return an error
        response with a non-200 status code.

        This decorator will return a 405 HTTP status code if the method is not
        POST.
        This decorator will return a 400 status code if the body contains
        invalid JSON.
        """
        @cls.handler
        @functools.wraps(func)
        def wrapper(self, request, suffix=''):
            """The wrapper function `json_handler` returns."""
            if request.method != "POST":
                return JsonHandlerError(405, "Method must be POST").get_response(allow=["POST"])
            try:
                request_json = json.loads(request.body)
            except ValueError:
                return JsonHandlerError(400, "Invalid JSON").get_response()
            try:
                response = func(self, request_json, suffix)
            except JsonHandlerError as err:
                return err.get_response()
            if isinstance(response, Response):
                return response
            else:
                return Response(json.dumps(response), content_type='application/json', charset='utf8')
        return wrapper

    @classmethod
    def handler(cls, func):
        """
        A decorator to indicate a function is usable as a handler.

        The wrapped function must return a `webob.Response` object.
        """
        func._is_xblock_handler = True      # pylint: disable=protected-access
        return func

    def handle(self, handler_name, request, suffix=''):
        """Handle `request` with this block's runtime."""
        return self.runtime.handle(self, handler_name, request, suffix)


class RuntimeServicesMixin(object):
    """
    This mixin provides all of the machinery needed for an XBlock-style object
    to declare dependencies on particular runtime services.
    """

    @class_lazy
    def _services_requested(cls):  # pylint: disable=no-self-argument
        """A per-class dictionary to store the services requested by a particular XBlock."""
        return {}

    @class_lazy
    def _combined_services(cls):  # pylint: disable=no-self-argument
        """
        A dictionary that collects all _services_requested by all ancestors of this XBlock class.
        """
        # The class declares what services it desires. To deal with subclasses,
        # especially mixins, properly, we have to walk up the inheritance
        # hierarchy, and combine all the declared services into one dictionary.
        combined = {}
        for parent in reversed(cls.mro()):
            combined.update(getattr(parent, "_services_requested", {}))
        return combined

    def __init__(self, runtime, **kwargs):
        """
        Arguments:

            runtime (:class:`.Runtime`): Use it to access the environment.
                It is available in XBlock code as ``self.runtime``.
        """
        self.runtime = runtime
        super(RuntimeServicesMixin, self).__init__(**kwargs)

    @classmethod
    def needs(cls, *service_names):
        """A class decorator to indicate that an XBlock class needs particular services."""
        def _decorator(cls_):                                # pylint: disable=missing-docstring
            for service_name in service_names:
                cls_._services_requested[service_name] = "need"  # pylint: disable=protected-access
            return cls_
        return _decorator

    @classmethod
    def wants(cls, *service_names):
        """A class decorator to indicate that an XBlock class wants particular services."""
        def _decorator(cls_):                                # pylint: disable=missing-docstring
            for service_name in service_names:
                cls_._services_requested[service_name] = "want"  # pylint: disable=protected-access
            return cls_
        return _decorator

    @classmethod
    def service_declaration(cls, service_name):
        """
        Find and return a service declaration.

        XBlocks declare their service requirements with `@XBlock.needs` and
        `@XBlock.wants` decorators.  These store information on the class.
        This function finds those declarations for a block.

        Arguments:
            service_name (str): the name of the service requested.

        Returns:
            One of "need", "want", or None.
        """
        return cls._combined_services.get(service_name)  # pylint: disable=no-member


@RuntimeServicesMixin.needs('field-data')
class ScopedStorageMixin(six.with_metaclass(NamedAttributesMetaclass, RuntimeServicesMixin)):
    """
    This mixin provides scope for Fields and the associated Scoped storage.
    """

    @class_lazy
    def fields(cls):  # pylint: disable=no-self-argument
        """
        A dictionary mapping the attribute name to the Field object for all
        Field attributes of the class.
        """
        fields = {}
        # Loop through all of the baseclasses of cls, in
        # the order that methods are resolved (Method Resolution Order / mro)
        # and find all of their defined fields.
        #
        # Only save the first such defined field (as expected for method resolution)

        bases = cls.mro()
        local = bases.pop(0)

        # First, descend the MRO from the top down, updating the 'fields' dictionary
        # so that the dictionary always has the most specific version of fields in it
        for base in reversed(bases):
            fields.update(getattr(base, 'fields', {}))

        # For this class, loop through all attributes not named 'fields',
        # find those of type Field, and save them to the 'fields' dict
        for attr_name, attr_value in inspect.getmembers(local, lambda attr: isinstance(attr, Field)):
            fields[attr_name] = attr_value

        return fields

    def __init__(self, scope_ids, field_data=None, **kwargs):
        """
        Arguments:
            field_data (:class:`.FieldData`): Interface used by the XBlock
                fields to access their data from wherever it is persisted.

            scope_ids (:class:`.ScopeIds`): Identifiers needed to resolve
                scopes.
        """
        # This is used to store a directly passed field data
        # for backwards compatibility
        if field_data:
            warnings.warn(
                "Setting _field_data via the constructor is deprecated, please use a Runtime service",
                FieldDataDeprecationWarning,
                stacklevel=2
            )
            # Storing _field_data instead of _deprecated_per_instance_field_data allows subclasses to
            # continue to override this behavior (for instance, the way that edx-platform's XModule does
            # in order to proxy to XBlock).
            self._field_data = field_data
        else:
            self._deprecated_per_instance_field_data = None  # pylint: disable=invalid-name

        self._field_data_cache = {}
        self._dirty_fields = {}
        self.scope_ids = scope_ids

        super(ScopedStorageMixin, self).__init__(**kwargs)

    @property
    def _field_data(self):
        """
        Return the FieldData for this XBlock (either as passed in the constructor
        or from retrieving the 'field-data' service).
        """
        if self._deprecated_per_instance_field_data:
            return self._deprecated_per_instance_field_data
        else:
            return self.runtime.service(self, 'field-data')

    @_field_data.setter
    def _field_data(self, field_data):
        """
        Set _field_data.

        Deprecated.
        """
        warnings.warn("Setting _field_data is deprecated", FieldDataDeprecationWarning, stacklevel=2)
        self._deprecated_per_instance_field_data = field_data

    def save(self):
        """Save all dirty fields attached to this XBlock."""
        if not self._dirty_fields:
            # nop if _dirty_fields attribute is empty
            return

        fields_to_save = self._get_fields_to_save()
        if fields_to_save:
            self.force_save_fields(fields_to_save)

    def force_save_fields(self, field_names):
        """
        Save all fields that are specified in `field_names`, even
        if they are not dirty.
        """
        fields = [self.fields[field_name] for field_name in field_names]
        fields_to_save_json = {}
        for field in fields:
            fields_to_save_json[field.name] = field.to_json(self._field_data_cache[field.name])

        try:
            # Throws KeyValueMultiSaveError if things go wrong
            self._field_data.set_many(self, fields_to_save_json)
        except KeyValueMultiSaveError as save_error:
            saved_fields = [field for field in fields
                            if field.name in save_error.saved_field_names]  # pylint: disable=exception-escape
            for field in saved_fields:
                # should only find one corresponding field
                fields.remove(field)
                # if the field was dirty, delete from dirty fields
                self._reset_dirty_field(field)
            msg = 'Error saving fields {}'.format(save_error.saved_field_names)
            raise XBlockSaveError(saved_fields, fields, msg)

        # Remove all dirty fields, since the save was successful
        for field in fields:
            self._reset_dirty_field(field)

    def _get_fields_to_save(self):
        """
        Get an xblock's dirty fields.
        """
        # If the field value isn't the same as the baseline we recorded
        # when it was read, then save it
        # pylint: disable=protected-access
        return [field.name for field in self._dirty_fields if field._is_dirty(self)]

    def _clear_dirty_fields(self):
        """
        Remove all dirty fields from an XBlock.
        """
        self._dirty_fields.clear()

    def _reset_dirty_field(self, field):
        """
        Resets dirty field value with the value from the field data cache.
        """
        if field in self._dirty_fields:
            self._dirty_fields[field] = copy.deepcopy(
                self._field_data_cache[field.name]
            )

    def __repr__(self):
        # `ScopedStorageMixin` obtains the `fields` attribute from the `ModelMetaclass`.
        # Since this is not understood by static analysis, silence this error.
        # pylint: disable=E1101
        attrs = []
        for field in six.itervalues(self.fields):
            try:
                value = getattr(self, field.name)
            except Exception:  # pylint: disable=broad-except
                # Ensure we return a string, even if unanticipated exceptions.
                attrs.append(" %s=???" % (field.name,))
            else:
                if isinstance(value, six.binary_type):
                    value = value.decode('utf-8', errors='escape')
                if isinstance(value, six.text_type):
                    value = value.strip()
                    if len(value) > 40:
                        value = value[:37] + "..."
                attrs.append(" %s=%r" % (field.name, value))
        return "<%s @%04X%s>" % (
            self.__class__.__name__,
            id(self) % 0xFFFF,
            ','.join(attrs)
        )


class ChildrenModelMetaclass(ScopedStorageMixin.__class__):
    """
    A metaclass that transforms the attribute `has_children = True` into a List
    field with a children scope.

    """
    def __new__(mcs, name, bases, attrs):
        if (attrs.get('has_children', False) or any(getattr(base, 'has_children', False) for base in bases)):
            attrs['children'] = ReferenceList(
                help='The ids of the children of this XBlock',
                scope=Scope.children)
        else:
            attrs['has_children'] = False

        return super(ChildrenModelMetaclass, mcs).__new__(mcs, name, bases, attrs)


class HierarchyMixin(six.with_metaclass(ChildrenModelMetaclass, ScopedStorageMixin)):
    """
    This adds Fields for parents and children.
    """

    parent = Reference(help='The id of the parent of this XBlock', default=None, scope=Scope.parent)

    def __init__(self, **kwargs):
        # A cache of the parent block, retrieved from .parent
        self._parent_block = None
        self._parent_block_id = None
        self._child_cache = {}

        for_parent = kwargs.pop('for_parent', None)

        if for_parent is not None:
            self._parent_block = for_parent
            self._parent_block_id = for_parent.scope_ids.usage_id

        super(HierarchyMixin, self).__init__(**kwargs)

    def get_parent(self):
        """Return the parent block of this block, or None if there isn't one."""
        if not self.has_cached_parent:
            if self.parent is not None:
                self._parent_block = self.runtime.get_block(self.parent)
            else:
                self._parent_block = None
            self._parent_block_id = self.parent
        return self._parent_block

    @property
    def has_cached_parent(self):
        """Return whether this block has a cached parent block."""
        return self.parent is not None and self._parent_block_id == self.parent

    def get_child(self, usage_id):
        """Return the child identified by ``usage_id``."""
        if usage_id in self._child_cache:
            return self._child_cache[usage_id]

        child_block = self.runtime.get_block(usage_id, for_parent=self)
        self._child_cache[usage_id] = child_block
        return child_block

    def get_children(self, usage_id_filter=None):
        """
        Return instantiated XBlocks for each of this blocks ``children``.
        """
        if not self.has_children:
            return []

        return [
            self.get_child(usage_id)
            for usage_id in self.children
            if usage_id_filter is None or usage_id_filter(usage_id)
        ]

    def clear_child_cache(self):
        """
        Reset the cache of children stored on this XBlock.
        """
        self._child_cache.clear()

    def add_children_to_node(self, node):
        """
        Add children to etree.Element `node`.
        """
        if self.has_children:
            for child_id in self.children:
                child = self.runtime.get_block(child_id)
                self.runtime.add_block_as_child_node(child, node)


class XmlSerializationMixin(ScopedStorageMixin):
    """
    A mixin that provides XML serialization and deserialization on top of ScopedStorage.
    """

    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Use `node` to construct a new block.

        Arguments:
            node (:class:`~xml.etree.ElementTree.Element`): The xml node to parse into an xblock.

            runtime (:class:`.Runtime`): The runtime to use while parsing.

            keys (:class:`.ScopeIds`): The keys identifying where this block
                will store its data.

            id_generator (:class:`.IdGenerator`): An object that will allow the
                runtime to generate correct definition and usage ids for
                children of this block.

        """
        block = runtime.construct_xblock_from_class(cls, keys)

        # The base implementation: child nodes become child blocks.
        # Or fields, if they belong to the right namespace.
        for child in node:
            if child.tag is etree.Comment:
                continue
            qname = etree.QName(child)
            tag = qname.localname
            namespace = qname.namespace

            if namespace == XML_NAMESPACES["option"]:
                cls._set_field_if_present(block, tag, child.text, child.attrib)
            else:
                block.runtime.add_node_as_child(block, child, id_generator)

        # Attributes become fields.
        for name, value in node.items():  # lxml has no iteritems
            cls._set_field_if_present(block, name, value, {})

        # Text content becomes "content", if such a field exists.
        if "content" in block.fields and block.fields["content"].scope == Scope.content:
            text = node.text
            if text:
                text = text.strip()
                if text:
                    block.content = text

        return block

    def add_xml_to_node(self, node):
        """
        For exporting, set data on `node` from ourselves.
        """
        # pylint: disable=E1101
        # Set node.tag based on our class name.
        node.tag = self.xml_element_name()
        node.set('xblock-family', self.entry_point)

        # Set node attributes based on our fields.
        for field_name, field in self.fields.items():
            if field_name in ('children', 'parent', 'content'):
                continue
            if field.is_set_on(self) or field.force_export:
                self._add_field(node, field_name, field)

        # A content field becomes text content.
        text = self.xml_text_content()
        if text is not None:
            node.text = text

    def xml_element_name(self):
        """What XML element name should be used for this block?"""
        return self.scope_ids.block_type

    def xml_text_content(self):
        """What is the text content for this block's XML node?"""
        # pylint: disable=E1101
        if 'content' in self.fields and self.content:
            return self.content
        else:
            return None

    @classmethod
    def _set_field_if_present(cls, block, name, value, attrs):
        """Sets the field block.name, if block have such a field."""
        if name in block.fields:
            value = (block.fields[name]).from_string(value)
            if "none" in attrs and attrs["none"] == "true":
                setattr(block, name, None)
            else:
                setattr(block, name, value)
        else:
            logging.warning("XBlock %s does not contain field %s", type(block), name)

    def _add_field(self, node, field_name, field):
        """
        Add xml representation of field to node.

        Depending on settings, it either stores the value of field
        as an xml attribute or creates a separate child node.
        """
        value = field.to_string(field.read_from(self))
        text_value = "" if value is None else value

        # Is the field type supposed to serialize the fact that the value is None to XML?
        save_none_as_xml_attr = field.none_to_xml and value is None
        field_attrs = {"none": "true"} if save_none_as_xml_attr else {}

        if save_none_as_xml_attr or field.xml_node:
            # Field will be output to XML as an separate element.
            tag = etree.QName(XML_NAMESPACES["option"], field_name)
            elem = etree.SubElement(node, tag, field_attrs)
            if field.xml_node:
                # Only set the value if forced via xml_node;
                # in all other cases, the value is None.
                # Avoids an unnecessary XML end tag.
                elem.text = text_value
        else:
            # Field will be output to XML as an attribute on the node.
            node.set(field_name, text_value)


class IndexInfoMixin(object):
    """
    This mixin provides interface for classes that wish to provide index
    information which might be used within a search index
    """

    def index_dictionary(self):
        """
        return key/value fields to feed an index within in a Python dict object
        values may be numeric / string or dict
        default implementation is an empty dict
        """
        return {}


class ViewsMixin(object):
    """
    This mixin provides decorators that can be used on xBlock view methods.
    """
    @classmethod
    def supports(cls, *functionalities):
        """
        A view decorator to indicate that an xBlock view has support for the
        given functionalities.

        Arguments:
            functionalities: String identifiers for the functionalities of the view.
                For example: "multi_device".
        """
        def _decorator(view):
            """
            Internal decorator that updates the given view's list of supported
            functionalities.
            """
            # pylint: disable=protected-access
            if not hasattr(view, "_supports"):
                view._supports = set()
            for functionality in functionalities:
                view._supports.add(functionality)
            return view
        return _decorator

    def has_support(self, view, functionality):
        """
        Returns whether the given view has support for the given functionality.

        An XBlock view declares support for a functionality with the
        @XBlock.supports decorator. The decorator stores information on the view.

        Note: We implement this as an instance method to allow xBlocks to
        override it, if necessary.

        Arguments:
            view (object): The view of the xBlock.
            functionality (str): A functionality of the view.
                For example: "multi_device".

        Returns:
            True or False
        """
        return hasattr(view, "_supports") and functionality in view._supports  # pylint: disable=protected-access
