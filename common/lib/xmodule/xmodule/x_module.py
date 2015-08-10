import logging
import os
import sys
import time
import yaml
import xml.sax.saxutils as saxutils

from contracts import contract, new_contract
from functools import partial
from lxml import etree
from collections import namedtuple
from pkg_resources import (
    resource_exists,
    resource_listdir,
    resource_string,
    resource_isdir,
)
from webob import Response
from webob.multidict import MultiDict
from lazy import lazy

from xblock.core import XBlock, XBlockAside
from xblock.fields import (
    Scope, Integer, Float, List,
    String, Dict, ScopeIds, Reference, ReferenceList,
    ReferenceValueDict, UserScope
)

from xblock.fragment import Fragment
from xblock.runtime import Runtime, IdReader, IdGenerator
from xmodule import block_metadata_utils
from xmodule.fields import RelativeTime
from xmodule.errortracker import exc_info_to_str
from xmodule.modulestore.exceptions import ItemNotFoundError

from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.asides import AsideUsageKeyV1, AsideDefinitionKeyV1
from xmodule.exceptions import UndefinedContext
import dogstats_wrapper as dog_stats_api

log = logging.getLogger(__name__)

XMODULE_METRIC_NAME = 'edxapp.xmodule'
XMODULE_DURATION_METRIC_NAME = XMODULE_METRIC_NAME + '.duration'
XMODULE_METRIC_SAMPLE_RATE = 0.1

# Stats event sent to DataDog in order to determine if old XML parsing can be deprecated.
DEPRECATION_VSCOMPAT_EVENT = 'deprecation.vscompat'

# xblock view names

# This is the view that will be rendered to display the XBlock in the LMS.
# It will also be used to render the block in "preview" mode in Studio, unless
# the XBlock also implements author_view.
STUDENT_VIEW = 'student_view'

# An optional view of the XBlock similar to student_view, but with possible inline
# editing capabilities. This view differs from studio_view in that it should be as similar to student_view
# as possible. When previewing XBlocks within Studio, Studio will prefer author_view to student_view.
AUTHOR_VIEW = 'author_view'

# The view used to render an editor in Studio. The editor rendering can be completely different
# from the LMS student_view, and it is only shown when the author selects "Edit".
STUDIO_VIEW = 'studio_view'

# Views that present a "preview" view of an xblock (as opposed to an editing view).
PREVIEW_VIEWS = [STUDENT_VIEW, AUTHOR_VIEW]


class OpaqueKeyReader(IdReader):
    """
    IdReader for :class:`DefinitionKey` and :class:`UsageKey`s.
    """
    def get_definition_id(self, usage_id):
        """Retrieve the definition that a usage is derived from.

        Args:
            usage_id: The id of the usage to query

        Returns:
            The `definition_id` the usage is derived from
        """
        raise NotImplementedError("Specific Modulestores must implement get_definition_id")

    def get_block_type(self, def_id):
        """Retrieve the block_type of a particular definition

        Args:
            def_id: The id of the definition to query

        Returns:
            The `block_type` of the definition
        """
        return def_id.block_type

    def get_usage_id_from_aside(self, aside_id):
        """
        Retrieve the XBlock `usage_id` associated with this aside usage id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `usage_id` of the usage the aside is commenting on.
        """
        return aside_id.usage_key

    def get_definition_id_from_aside(self, aside_id):
        """
        Retrieve the XBlock `definition_id` associated with this aside definition id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `definition_id` of the usage the aside is commenting on.
        """
        return aside_id.definition_key

    def get_aside_type_from_usage(self, aside_id):
        """
        Retrieve the XBlockAside `aside_type` associated with this aside
        usage id.

        Args:
            aside_id: The usage id of the XBlockAside.

        Returns:
            The `aside_type` of the aside.
        """
        return aside_id.aside_type

    def get_aside_type_from_definition(self, aside_id):
        """
        Retrieve the XBlockAside `aside_type` associated with this aside
        definition id.

        Args:
            aside_id: The definition id of the XBlockAside.

        Returns:
            The `aside_type` of the aside.
        """
        return aside_id.aside_type


class AsideKeyGenerator(IdGenerator):
    """
    An :class:`.IdGenerator` that only provides facilities for constructing new XBlockAsides.
    """
    def create_aside(self, definition_id, usage_id, aside_type):
        """
        Make a new aside definition and usage ids, indicating an :class:`.XBlockAside` of type `aside_type`
        commenting on an :class:`.XBlock` usage `usage_id`

        Returns:
            (aside_definition_id, aside_usage_id)
        """
        def_key = AsideDefinitionKeyV1(definition_id, aside_type)
        usage_key = AsideUsageKeyV1(usage_id, aside_type)
        return (def_key, usage_key)

    def create_usage(self, def_id):
        """Make a usage, storing its definition id.

        Returns the newly-created usage id.
        """
        raise NotImplementedError("Specific Modulestores must provide implementations of create_usage")

    def create_definition(self, block_type, slug=None):
        """Make a definition, storing its block type.

        If `slug` is provided, it is a suggestion that the definition id
        incorporate the slug somehow.

        Returns the newly-created definition id.

        """
        raise NotImplementedError("Specific Modulestores must provide implementations of create_definition")


def dummy_track(_event_type, _event):
    pass


class HTMLSnippet(object):
    """
    A base class defining an interface for an object that is able to present an
    html snippet, along with associated javascript and css
    """

    js = {}
    js_module_name = None

    css = {}

    @classmethod
    def get_javascript(cls):
        """
        Return a dictionary containing some of the following keys:

            coffee: A list of coffeescript fragments that should be compiled and
                    placed on the page

            js: A list of javascript fragments that should be included on the
            page

        All of these will be loaded onto the page in the CMS
        """
        # cdodge: We've moved the xmodule.coffee script from an outside directory into the xmodule area of common
        # this means we need to make sure that all xmodules include this dependency which had been previously implicitly
        # fulfilled in a different area of code
        coffee = cls.js.setdefault('coffee', [])
        js = cls.js.setdefault('js', [])

        # Added xmodule.js separately to enforce 000 prefix for this only.
        cls.js.setdefault('xmodule_js', resource_string(__name__, 'js/src/xmodule.js'))

        return cls.js

    @classmethod
    def get_css(cls):
        """
        Return a dictionary containing some of the following keys:

            css: A list of css fragments that should be applied to the html
                 contents of the snippet

            sass: A list of sass fragments that should be applied to the html
                  contents of the snippet

            scss: A list of scss fragments that should be applied to the html
                  contents of the snippet
        """
        return cls.css

    def get_html(self):
        """
        Return the html used to display this snippet
        """
        raise NotImplementedError(
            "get_html() must be provided by specific modules - not present in {0}"
            .format(self.__class__))


def shim_xmodule_js(block, fragment):
    """
    Set up the XBlock -> XModule shim on the supplied :class:`xblock.fragment.Fragment`
    """
    if not fragment.js_init_fn:
        fragment.initialize_js('XBlockToXModuleShim')
        fragment.json_init_args = {'xmodule-type': block.js_module_name}


class XModuleFields(object):
    """
    Common fields for XModules.
    """
    display_name = String(
        display_name="Display Name",
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings,
        # it'd be nice to have a useful default but it screws up other things; so,
        # use display_name_with_default for those
        default=None
    )


class XModuleMixin(XModuleFields, XBlock):
    """
    Fields and methods used by XModules internally.

    Adding this Mixin to an :class:`XBlock` allows it to cooperate with old-style :class:`XModules`
    """
    # Attributes for inspection of the descriptor

    # This indicates whether the xmodule is a problem-type.
    # It should respond to max_score() and grade(). It can be graded or ungraded
    # (like a practice problem).
    has_score = False

    # Whether this module can be displayed in read-only mode.  It is safe to set this to True if
    # all user state is handled through the FieldData API.
    show_in_read_only_mode = False

    # Class level variable

    # True if this descriptor always requires recalculation of grades, for
    # example if the score can change via an extrnal service, not just when the
    # student interacts with the module on the page.  A specific example is
    # FoldIt, which posts grade-changing updates through a separate API.
    always_recalculate_grades = False
    # The default implementation of get_icon_class returns the icon_class
    # attribute of the class
    #
    # This attribute can be overridden by subclasses, and
    # the function can also be overridden if the icon class depends on the data
    # in the module
    icon_class = 'other'

    def __init__(self, *args, **kwargs):
        self.xmodule_runtime = None
        self._asides = []

        super(XModuleMixin, self).__init__(*args, **kwargs)

    @property
    def runtime(self):
        return CombinedSystem(self.xmodule_runtime, self._runtime)

    @runtime.setter
    def runtime(self, value):
        self._runtime = value

    @property
    def system(self):
        """
        Return the XBlock runtime (backwards compatibility alias provided for XModules).
        """
        return self.runtime

    @property
    def course_id(self):
        return self.location.course_key

    @property
    def category(self):
        return self.scope_ids.block_type

    @property
    def location(self):
        return self.scope_ids.usage_id

    @location.setter
    def location(self, value):
        assert isinstance(value, UsageKey)
        self.scope_ids = self.scope_ids._replace(
            def_id=value,
            usage_id=value,
        )

    @property
    def url_name(self):
        return block_metadata_utils.url_name_for_block(self)

    @property
    def display_name_with_default(self):
        """
        Return a display name for the module: use display_name if defined in
        metadata, otherwise convert the url name.
        """
        return block_metadata_utils.display_name_with_default(self)

    @property
    def display_name_with_default_escaped(self):
        """
        DEPRECATED: use display_name_with_default

        Return an html escaped display name for the module: use display_name if
        defined in metadata, otherwise convert the url name.

        Note: This newly introduced method should not be used.  It was only
        introduced to enable a quick search/replace and the ability to slowly
        migrate and test switching to display_name_with_default, which is no
        longer escaped.
        """
        return block_metadata_utils.display_name_with_default_escaped(self)

    @property
    def tooltip_title(self):
        """
        Return the title for the sequence item containing this xmodule as its top level item.
        """
        return self.display_name_with_default

    @property
    def xblock_kvs(self):
        """
        Retrieves the internal KeyValueStore for this XModule.

        Should only be used by the persistence layer. Use with caution.
        """
        # if caller wants kvs, caller's assuming it's up to date; so, decache it
        self.save()
        return self._field_data._kvs  # pylint: disable=protected-access

    @lazy
    def _unwrapped_field_data(self):
        """
        This property hold the value _field_data here before we wrap it in
        the LmsFieldData or OverrideFieldData classes.
        """
        return self._field_data

    def add_aside(self, aside):
        """
        save connected asides
        """
        self._asides.append(aside)

    def get_asides(self):
        """
        get the list of connected asides
        """
        return self._asides

    def get_explicitly_set_fields_by_scope(self, scope=Scope.content):
        """
        Get a dictionary of the fields for the given scope which are set explicitly on this xblock. (Including
        any set to None.)
        """
        result = {}
        for field in self.fields.values():
            if field.scope == scope and field.is_set_on(self):
                try:
                    result[field.name] = field.read_json(self)
                except TypeError as exception:
                    exception_message = "{message}, Block-location:{location}, Field-name:{field_name}".format(
                        message=exception.message,
                        location=unicode(self.location),
                        field_name=field.name
                    )
                    raise TypeError(exception_message)
        return result

    def has_children_at_depth(self, depth):
        r"""
        Returns true if self has children at the given depth. depth==0 returns
        false if self is a leaf, true otherwise.

                           SELF
                            |
                     [child at depth 0]
                     /           \
                 [depth 1]    [depth 1]
                 /       \
           [depth 2]   [depth 2]

        So the example above would return True for `has_children_at_depth(2)`, and False
        for depth > 2
        """
        if depth < 0:
            raise ValueError("negative depth argument is invalid")
        elif depth == 0:
            return bool(self.get_children())
        else:
            return any(child.has_children_at_depth(depth - 1) for child in self.get_children())

    def get_content_titles(self):
        r"""
        Returns list of content titles for all of self's children.

                         SEQUENCE
                            |
                         VERTICAL
                        /        \
                 SPLIT_TEST      DISCUSSION
                /        \
           VIDEO A      VIDEO B

        Essentially, this function returns a list of display_names (e.g. content titles)
        for all of the leaf nodes.  In the diagram above, calling get_content_titles on
        SEQUENCE would return the display_names of `VIDEO A`, `VIDEO B`, and `DISCUSSION`.

        This is most obviously useful for sequence_modules, which need this list to display
        tooltips to users, though in theory this should work for any tree that needs
        the display_names of all its leaf nodes.
        """
        if self.has_children:
            return sum((child.get_content_titles() for child in self.get_children()), [])
        else:
            return [self.display_name_with_default_escaped]

    def get_children(self, usage_id_filter=None, usage_key_filter=None):  # pylint: disable=arguments-differ
        """Returns a list of XBlock instances for the children of
        this module"""

        # Be backwards compatible with callers using usage_key_filter
        if usage_id_filter is None and usage_key_filter is not None:
            usage_id_filter = usage_key_filter

        return [
            child
            for child
            in super(XModuleMixin, self).get_children(usage_id_filter)
            if child is not None
        ]

    def get_child(self, usage_id):
        """
        Return the child XBlock identified by ``usage_id``, or ``None`` if there
        is an error while retrieving the block.
        """
        try:
            child = super(XModuleMixin, self).get_child(usage_id)
        except ItemNotFoundError:
            log.warning(u'Unable to load item %s, skipping', usage_id)
            dog_stats_api.increment(
                "xmodule.item_not_found_error",
                tags=[
                    u"course_id:{}".format(usage_id.course_key),
                    u"block_type:{}".format(usage_id.block_type),
                    u"parent_block_type:{}".format(self.location.block_type),
                ]
            )
            return None

        if child is None:
            return None

        child.runtime.export_fs = self.runtime.export_fs
        return child

    def get_required_module_descriptors(self):
        """Returns a list of XModuleDescriptor instances upon which this module depends, but are
        not children of this module"""
        return []

    def get_display_items(self):
        """
        Returns a list of descendent module instances that will display
        immediately inside this module.
        """
        items = []
        for child in self.get_children():
            items.extend(child.displayable_items())

        return items

    def displayable_items(self):
        """
        Returns list of displayable modules contained by this module. If this
        module is visible, should return [self].
        """
        return [self]

    def get_child_by(self, selector):
        """
        Return a child XBlock that matches the specified selector
        """
        for child in self.get_children():
            if selector(child):
                return child
        return None

    def get_icon_class(self):
        """
        Return a css class identifying this module in the context of an icon
        """
        return self.icon_class

    def has_dynamic_children(self):
        """
        Returns True if this descriptor has dynamic children for a given
        student when the module is created.

        Returns False if the children of this descriptor are the same
        children that the module will return for any student.
        """
        return False

    # Functions used in the LMS

    def get_score(self):
        """
        Score the student received on the problem, or None if there is no
        score.

        Returns:
          dictionary
             {'score': integer, from 0 to get_max_score(),
              'total': get_max_score()}

          NOTE (vshnayder): not sure if this was the intended return value, but
          that's what it's doing now.  I suspect that we really want it to just
          return a number.  Would need to change (at least) capa to match if we did that.
        """
        return None

    def max_score(self):
        """ Maximum score. Two notes:

            * This is generic; in abstract, a problem could be 3/5 points on one
              randomization, and 5/7 on another

            * In practice, this is a Very Bad Idea, and (a) will break some code
              in place (although that code should get fixed), and (b) break some
              analytics we plan to put in place.
        """
        return None

    def get_progress(self):
        """ Return a progress.Progress object that represents how far the
        student has gone in this module.  Must be implemented to get correct
        progress tracking behavior in nesting modules like sequence and
        vertical.

        If this module has no notion of progress, return None.
        """
        return None

    def bind_for_student(self, xmodule_runtime, user_id, wrappers=None):
        """
        Set up this XBlock to act as an XModule instead of an XModuleDescriptor.

        Arguments:
            xmodule_runtime (:class:`ModuleSystem'): the runtime to use when accessing student facing methods
            user_id: The user_id to set in scope_ids
            wrappers: These are a list functions that put a wrapper, such as
                      LmsFieldData or OverrideFieldData, around the field_data.
                      Note that the functions will be applied in the order in
                      which they're listed. So [f1, f2] -> f2(f1(field_data))
        """
        # pylint: disable=attribute-defined-outside-init

        # Skip rebinding if we're already bound a user, and it's this user.
        if self.scope_ids.user_id is not None and user_id == self.scope_ids.user_id:
            if getattr(xmodule_runtime, 'position', None):
                self.position = xmodule_runtime.position   # update the position of the tab
            return

        # If we are switching users mid-request, save the data from the old user.
        self.save()

        # Update scope_ids to point to the new user.
        self.scope_ids = self.scope_ids._replace(user_id=user_id)

        # Clear out any cached instantiated children.
        self.clear_child_cache()

        # Clear out any cached field data scoped to the old user.
        for field in self.fields.values():
            if field.scope in (Scope.parent, Scope.children):
                continue

            if field.scope.user == UserScope.ONE:
                field._del_cached_value(self)  # pylint: disable=protected-access
                # not the most elegant way of doing this, but if we're removing
                # a field from the module's field_data_cache, we should also
                # remove it from its _dirty_fields
                if field in self._dirty_fields:
                    del self._dirty_fields[field]

        # Set the new xmodule_runtime and field_data (which are user-specific)
        self.xmodule_runtime = xmodule_runtime

        if wrappers is None:
            wrappers = []

        wrapped_field_data = self._unwrapped_field_data
        for wrapper in wrappers:
            wrapped_field_data = wrapper(wrapped_field_data)

        self._field_data = wrapped_field_data

    @property
    def non_editable_metadata_fields(self):
        """
        Return the list of fields that should not be editable in Studio.

        When overriding, be sure to append to the superclasses' list.
        """
        # We are not allowing editing of xblock tag and name fields at this time (for any component).
        return [XBlock.tags, XBlock.name]

    @property
    def editable_metadata_fields(self):
        """
        Returns the metadata fields to be edited in Studio. These are fields with scope `Scope.settings`.

        Can be limited by extending `non_editable_metadata_fields`.
        """
        metadata_fields = {}

        # Only use the fields from this class, not mixins
        fields = getattr(self, 'unmixed_class', self.__class__).fields

        for field in fields.values():
            if field in self.non_editable_metadata_fields:
                continue
            if field.scope not in (Scope.settings, Scope.content):
                continue

            metadata_fields[field.name] = self._create_metadata_editor_info(field)

        return metadata_fields

    def _create_metadata_editor_info(self, field):
        """
        Creates the information needed by the metadata editor for a specific field.
        """
        def jsonify_value(field, json_choice):
            """
            Convert field value to JSON, if needed.
            """
            if isinstance(json_choice, dict):
                new_json_choice = dict(json_choice)  # make a copy so below doesn't change the original
                if 'display_name' in json_choice:
                    new_json_choice['display_name'] = get_text(json_choice['display_name'])
                if 'value' in json_choice:
                    new_json_choice['value'] = field.to_json(json_choice['value'])
            else:
                new_json_choice = field.to_json(json_choice)
            return new_json_choice

        def get_text(value):
            """Localize a text value that might be None."""
            if value is None:
                return None
            else:
                return self.runtime.service(self, "i18n").ugettext(value)

        # gets the 'default_value' and 'explicitly_set' attrs
        metadata_field_editor_info = self.runtime.get_field_provenance(self, field)
        metadata_field_editor_info['field_name'] = field.name
        metadata_field_editor_info['display_name'] = get_text(field.display_name)
        metadata_field_editor_info['help'] = get_text(field.help)
        metadata_field_editor_info['value'] = field.read_json(self)

        # We support the following editors:
        # 1. A select editor for fields with a list of possible values (includes Booleans).
        # 2. Number editors for integers and floats.
        # 3. A generic string editor for anything else (editing JSON representation of the value).
        editor_type = "Generic"
        values = field.values
        if "values_provider" in field.runtime_options:
            values = field.runtime_options['values_provider'](self)
        if isinstance(values, (tuple, list)) and len(values) > 0:
            editor_type = "Select"
            values = [jsonify_value(field, json_choice) for json_choice in values]
        elif isinstance(field, Integer):
            editor_type = "Integer"
        elif isinstance(field, Float):
            editor_type = "Float"
        elif isinstance(field, List):
            editor_type = "List"
        elif isinstance(field, Dict):
            editor_type = "Dict"
        elif isinstance(field, RelativeTime):
            editor_type = "RelativeTime"
        elif isinstance(field, String) and field.name == "license":
            editor_type = "License"
        metadata_field_editor_info['type'] = editor_type
        metadata_field_editor_info['options'] = [] if values is None else values

        return metadata_field_editor_info


class ProxyAttribute(object):
    """
    A (python) descriptor that proxies attribute access.

    For example:

    class Foo(object):
        def __init__(self, value):
            self.foo_attr = value

    class Bar(object):
        foo = Foo('x')
        foo_attr = ProxyAttribute('foo', 'foo_attr')

    bar = Bar()

    assert bar.foo_attr == 'x'
    bar.foo_attr = 'y'
    assert bar.foo.foo_attr == 'y'
    del bar.foo_attr
    assert not hasattr(bar.foo, 'foo_attr')
    """
    def __init__(self, source, name):
        """
        :param source: The name of the attribute to proxy to
        :param name: The name of the attribute to proxy
        """
        self._source = source
        self._name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(getattr(instance, self._source), self._name)

    def __set__(self, instance, value):
        setattr(getattr(instance, self._source), self._name, value)

    def __delete__(self, instance):
        delattr(getattr(instance, self._source), self._name)


module_attr = partial(ProxyAttribute, '_xmodule')  # pylint: disable=invalid-name
descriptor_attr = partial(ProxyAttribute, 'descriptor')  # pylint: disable=invalid-name
module_runtime_attr = partial(ProxyAttribute, 'xmodule_runtime')  # pylint: disable=invalid-name


@XBlock.needs("i18n")
class XModule(HTMLSnippet, XModuleMixin):
    """ Implements a generic learning module.

        Subclasses must at a minimum provide a definition for get_html in order
        to be displayed to users.

        See the HTML module for a simple example.
    """

    entry_point = "xmodule.v1"

    has_score = descriptor_attr('has_score')
    show_in_read_only_mode = descriptor_attr('show_in_read_only_mode')
    _field_data_cache = descriptor_attr('_field_data_cache')
    _field_data = descriptor_attr('_field_data')
    _dirty_fields = descriptor_attr('_dirty_fields')

    def __init__(self, descriptor, *args, **kwargs):
        """
        Construct a new xmodule

        runtime: An XBlock runtime allowing access to external resources

        descriptor: the XModuleDescriptor that this module is an instance of.

        field_data: A dictionary-like object that maps field names to values
            for those fields.
        """

        # Set the descriptor first so that we can proxy to it
        self.descriptor = descriptor
        self._runtime = None
        super(XModule, self).__init__(*args, **kwargs)
        self.runtime.xmodule_instance = self

    @property
    def runtime(self):
        return CombinedSystem(self._runtime, self.descriptor._runtime)  # pylint: disable=protected-access

    @runtime.setter
    def runtime(self, value):  # pylint: disable=arguments-differ
        self._runtime = value

    def __unicode__(self):
        return u'<x_module(id={0})>'.format(self.id)

    def handle_ajax(self, _dispatch, _data):
        """ dispatch is last part of the URL.
            data is a dictionary-like object with the content of the request"""
        return u""

    @XBlock.handler
    def xmodule_handler(self, request, suffix=None):
        """
        XBlock handler that wraps `handle_ajax`
        """
        class FileObjForWebobFiles(object):
            """
            Turn Webob cgi.FieldStorage uploaded files into pure file objects.

            Webob represents uploaded files as cgi.FieldStorage objects, which
            have a .file attribute.  We wrap the FieldStorage object, delegating
            attribute access to the .file attribute.  But the files have no
            name, so we carry the FieldStorage .filename attribute as the .name.

            """
            def __init__(self, webob_file):
                self.file = webob_file.file
                self.name = webob_file.filename

            def __getattr__(self, name):
                return getattr(self.file, name)

        # WebOb requests have multiple entries for uploaded files.  handle_ajax
        # expects a single entry as a list.
        request_post = MultiDict(request.POST)
        for key in set(request.POST.iterkeys()):
            if hasattr(request.POST[key], "file"):
                request_post[key] = map(FileObjForWebobFiles, request.POST.getall(key))

        response_data = self.handle_ajax(suffix, request_post)
        return Response(response_data, content_type='application/json')

    def get_child(self, usage_id):
        if usage_id in self._child_cache:
            return self._child_cache[usage_id]

        # Take advantage of the children cache that the descriptor might have
        child_descriptor = self.descriptor.get_child(usage_id)
        child_block = None
        if child_descriptor is not None:
            child_block = self.system.get_module(child_descriptor)

        self._child_cache[usage_id] = child_block
        return child_block

    def get_child_descriptors(self):
        """
        Returns the descriptors of the child modules

        Overriding this changes the behavior of get_children and
        anything that uses get_children, such as get_display_items.

        This method will not instantiate the modules of the children
        unless absolutely necessary, so it is cheaper to call than get_children

        These children will be the same children returned by the
        descriptor unless descriptor.has_dynamic_children() is true.
        """
        return self.descriptor.get_children()

    def displayable_items(self):
        """
        Returns list of displayable modules contained by this module. If this
        module is visible, should return [self].
        """
        return [self.descriptor]

    # ~~~~~~~~~~~~~~~ XBlock API Wrappers ~~~~~~~~~~~~~~~~
    def student_view(self, context):
        """
        Return a fragment with the html from this XModule

        Doesn't yet add any of the javascript to the fragment, nor the css.
        Also doesn't expect any javascript binding, yet.

        Makes no use of the context parameter
        """
        return Fragment(self.get_html())


def policy_key(location):
    """
    Get the key for a location in a policy file.  (Since the policy file is
    specific to a course, it doesn't need the full location url).
    """
    return u'{cat}/{name}'.format(cat=location.category, name=location.name)


Template = namedtuple("Template", "metadata data children")


class ResourceTemplates(object):
    """
    Gets the templates associated w/ a containing cls. The cls must have a 'template_dir_name' attribute.
    It finds the templates as directly in this directory under 'templates'.
    """
    template_packages = [__name__]

    @classmethod
    def templates(cls):
        """
        Returns a list of dictionary field: value objects that describe possible templates that can be used
        to seed a module of this type.

        Expects a class attribute template_dir_name that defines the directory
        inside the 'templates' resource directory to pull templates from
        """
        templates = []
        dirname = cls.get_template_dir()
        if dirname is not None:
            for pkg in cls.template_packages:
                if not resource_isdir(pkg, dirname):
                    continue
                for template_file in resource_listdir(pkg, dirname):
                    if not template_file.endswith('.yaml'):
                        log.warning("Skipping unknown template file %s", template_file)
                        continue
                    template_content = resource_string(pkg, os.path.join(dirname, template_file))
                    template = yaml.safe_load(template_content)
                    template['template_id'] = template_file
                    templates.append(template)
        return templates

    @classmethod
    def get_template_dir(cls):
        if getattr(cls, 'template_dir_name', None):
            dirname = os.path.join('templates', cls.template_dir_name)
            if not resource_isdir(__name__, dirname):
                log.warning(u"No resource directory {dir} found when loading {cls_name} templates".format(
                    dir=dirname,
                    cls_name=cls.__name__,
                ))
                return None
            else:
                return dirname
        else:
            return None

    @classmethod
    def get_template(cls, template_id):
        """
        Get a single template by the given id (which is the file name identifying it w/in the class's
        template_dir_name)

        """
        dirname = cls.get_template_dir()
        if dirname is not None:
            path = os.path.join(dirname, template_id)
            for pkg in cls.template_packages:
                if resource_exists(pkg, path):
                    template_content = resource_string(pkg, path)
                    template = yaml.safe_load(template_content)
                    template['template_id'] = template_id
                    return template


@XBlock.needs("i18n")
class XModuleDescriptor(HTMLSnippet, ResourceTemplates, XModuleMixin):
    """
    An XModuleDescriptor is a specification for an element of a course. This
    could be a problem, an organizational element (a group of content), or a
    segment of video, for example.

    XModuleDescriptors are independent and agnostic to the current student state
    on a problem. They handle the editing interface used by instructors to
    create a problem, and can generate XModules (which do know about student
    state).
    """

    entry_point = "xmodule.v1"

    module_class = XModule

    # VS[compat].  Backwards compatibility code that can go away after
    # importing 2012 courses.
    # A set of metadata key conversions that we want to make
    metadata_translations = {
        'slug': 'url_name',
        'name': 'display_name',
    }

    # ============================= STRUCTURAL MANIPULATION ===================
    def __init__(self, *args, **kwargs):
        """
        Construct a new XModuleDescriptor. The only required arguments are the
        system, used for interaction with external resources, and the
        definition, which specifies all the data needed to edit and display the
        problem (but none of the associated metadata that handles recordkeeping
        around the problem).

        This allows for maximal flexibility to add to the interface while
        preserving backwards compatibility.

        runtime: A DescriptorSystem for interacting with external resources

        field_data: A dictionary-like object that maps field names to values
            for those fields.

        XModuleDescriptor.__init__ takes the same arguments as xblock.core:XBlock.__init__
        """
        super(XModuleDescriptor, self).__init__(*args, **kwargs)
        # update_version is the version which last updated this xblock v prev being the penultimate updater
        # leaving off original_version since it complicates creation w/o any obv value yet and is computable
        # by following previous until None
        # definition_locator is only used by mongostores which separate definitions from blocks
        self.previous_version = self.update_version = self.definition_locator = None
        self.xmodule_runtime = None

    @classmethod
    def _translate(cls, key):
        'VS[compat]'
        if key in cls.metadata_translations:
            dog_stats_api.increment(
                DEPRECATION_VSCOMPAT_EVENT,
                tags=["location:xmodule_descriptor_translate"]
            )
        return cls.metadata_translations.get(key, key)

    # ================================= XML PARSING ============================
    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Interpret the parsed XML in `node`, creating an XModuleDescriptor.
        """
        # It'd be great to not reserialize and deserialize the xml
        xml = etree.tostring(node)
        block = cls.from_xml(xml, runtime, id_generator)
        return block

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
        raise NotImplementedError('Modules must implement from_xml to be parsable from xml')

    def add_xml_to_node(self, node):
        """
        Export this :class:`XModuleDescriptor` as XML, by setting attributes on the provided
        `node`.
        """
        xml_string = self.export_to_xml(self.runtime.export_fs)
        exported_node = etree.fromstring(xml_string)
        node.tag = exported_node.tag
        node.text = exported_node.text
        node.tail = exported_node.tail
        for key, value in exported_node.items():
            node.set(key, value)

        node.extend(list(exported_node))

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
        raise NotImplementedError('Modules must implement export_to_xml to enable xml export')

    def editor_saved(self, user, old_metadata, old_content):
        """
        This method is called when "Save" is pressed on the Studio editor.

        Note that after this method is called, the modulestore update_item method will
        be called on this xmodule. Therefore, any modifications to the xmodule that are
        performed in editor_saved will automatically be persisted (calling update_item
        from implementors of this method is not necessary).

        Args:
            user: the user who requested the save (as obtained from the request)
            old_metadata (dict): the values of the fields with Scope.settings before the save was performed
            old_content (dict): the values of the fields with Scope.content before the save was performed.
                This will include 'data'.
        """
        pass

    # =============================== BUILTIN METHODS ==========================
    def __eq__(self, other):
        return (hasattr(other, 'scope_ids') and
                self.scope_ids == other.scope_ids and
                self.fields.keys() == other.fields.keys() and
                all(getattr(self, field.name) == getattr(other, field.name)
                    for field in self.fields.values()))

    def __repr__(self):
        return (
            "{0.__class__.__name__}("
            "{0.runtime!r}, "
            "{0._field_data!r}, "
            "{0.scope_ids!r}"
            ")".format(self)
        )

    # ~~~~~~~~~~~~~~~ XModule Indirection ~~~~~~~~~~~~~~~~
    @property
    def _xmodule(self):
        """
        Returns the XModule corresponding to this descriptor. Expects that the system
        already supports all of the attributes needed by xmodules
        """
        if self.xmodule_runtime is None:
            raise UndefinedContext()
        assert self.xmodule_runtime.error_descriptor_class is not None
        if self.xmodule_runtime.xmodule_instance is None:
            try:
                self.xmodule_runtime.construct_xblock_from_class(
                    self.module_class,
                    descriptor=self,
                    scope_ids=self.scope_ids,
                    field_data=self._field_data,
                    for_parent=self.get_parent() if self.has_cached_parent else None
                )
                self.xmodule_runtime.xmodule_instance.save()
            except Exception:  # pylint: disable=broad-except
                # xmodule_instance is set by the XModule.__init__. If we had an error after that,
                # we need to clean it out so that we can set up the ErrorModule instead
                self.xmodule_runtime.xmodule_instance = None

                if isinstance(self, self.xmodule_runtime.error_descriptor_class):
                    log.exception('Error creating an ErrorModule from an ErrorDescriptor')
                    raise

                log.exception('Error creating xmodule')
                descriptor = self.xmodule_runtime.error_descriptor_class.from_descriptor(
                    self,
                    error_msg=exc_info_to_str(sys.exc_info())
                )
                descriptor.xmodule_runtime = self.xmodule_runtime
                self.xmodule_runtime.xmodule_instance = descriptor._xmodule  # pylint: disable=protected-access
        return self.xmodule_runtime.xmodule_instance

    course_id = module_attr('course_id')
    displayable_items = module_attr('displayable_items')
    get_display_items = module_attr('get_display_items')
    get_icon_class = module_attr('get_icon_class')
    get_progress = module_attr('get_progress')
    get_score = module_attr('get_score')
    handle_ajax = module_attr('handle_ajax')
    max_score = module_attr('max_score')
    student_view = module_attr(STUDENT_VIEW)
    get_child_descriptors = module_attr('get_child_descriptors')
    xmodule_handler = module_attr('xmodule_handler')

    # ~~~~~~~~~~~~~~~ XBlock API Wrappers ~~~~~~~~~~~~~~~~
    def studio_view(self, _context):
        """
        Return a fragment with the html from this XModuleDescriptor's editing view

        Doesn't yet add any of the javascript to the fragment, nor the css.
        Also doesn't expect any javascript binding, yet.

        Makes no use of the context parameter
        """
        return Fragment(self.get_html())


class ConfigurableFragmentWrapper(object):
    """
    Runtime mixin that allows for composition of many `wrap_xblock` wrappers
    """
    def __init__(self, wrappers=None, wrappers_asides=None, **kwargs):
        """
        :param wrappers: A list of wrappers, where each wrapper is:

            def wrapper(block, view, frag, context):
                ...
                return wrapped_frag
        """
        super(ConfigurableFragmentWrapper, self).__init__(**kwargs)
        if wrappers is not None:
            self.wrappers = wrappers
        else:
            self.wrappers = []
        if wrappers_asides is not None:
            self.wrappers_asides = wrappers_asides
        else:
            self.wrappers_asides = []

    def wrap_xblock(self, block, view, frag, context):
        """
        See :func:`Runtime.wrap_child`
        """
        for wrapper in self.wrappers:
            frag = wrapper(block, view, frag, context)

        return frag

    def wrap_aside(self, block, aside, view, frag, context):    # pylint: disable=unused-argument
        """
        See :func:`Runtime.wrap_child`
        """
        for wrapper in self.wrappers_asides:
            frag = wrapper(aside, view, frag, context)

        return frag


# This function exists to give applications (LMS/CMS) a place to monkey-patch until
# we can refactor modulestore to split out the FieldData half of its interface from
# the Runtime part of its interface. This function mostly matches the
# Runtime.handler_url interface.
#
# The monkey-patching happens in (lms|cms)/startup.py
def descriptor_global_handler_url(block, handler_name, suffix='', query='', thirdparty=False):  # pylint: disable=unused-argument
    """
    See :meth:`xblock.runtime.Runtime.handler_url`.
    """
    raise NotImplementedError("Applications must monkey-patch this function before using handler_url for studio_view")


# This function exists to give applications (LMS/CMS) a place to monkey-patch until
# we can refactor modulestore to split out the FieldData half of its interface from
# the Runtime part of its interface. This function matches the Runtime.local_resource_url interface
#
# The monkey-patching happens in (lms|cms)/startup.py
def descriptor_global_local_resource_url(block, uri):  # pylint: disable=invalid-name, unused-argument
    """
    See :meth:`xblock.runtime.Runtime.local_resource_url`.
    """
    raise NotImplementedError("Applications must monkey-patch this function before using local_resource_url for studio_view")


class MetricsMixin(object):
    """
    Mixin for adding metric logging for render and handle methods in the DescriptorSystem and ModuleSystem.
    """

    def render(self, block, view_name, context=None):
        start_time = time.time()
        try:
            status = "success"
            return super(MetricsMixin, self).render(block, view_name, context=context)

        except:
            status = "failure"
            raise

        finally:
            end_time = time.time()
            duration = end_time - start_time
            course_id = getattr(self, 'course_id', '')
            tags = [
                u'view_name:{}'.format(view_name),
                u'action:render',
                u'action_status:{}'.format(status),
                u'course_id:{}'.format(course_id),
                u'block_type:{}'.format(block.scope_ids.block_type),
                u'block_family:{}'.format(block.entry_point),
            ]
            dog_stats_api.increment(XMODULE_METRIC_NAME, tags=tags, sample_rate=XMODULE_METRIC_SAMPLE_RATE)
            dog_stats_api.histogram(
                XMODULE_DURATION_METRIC_NAME,
                duration,
                tags=tags,
                sample_rate=XMODULE_METRIC_SAMPLE_RATE,
            )
            log.debug(
                "%.3fs - render %s.%s (%s)",
                duration,
                block.__class__.__name__,
                view_name,
                getattr(block, 'location', ''),
            )

    def handle(self, block, handler_name, request, suffix=''):
        start_time = time.time()
        try:
            status = "success"
            return super(MetricsMixin, self).handle(block, handler_name, request, suffix=suffix)

        except:
            status = "failure"
            raise

        finally:
            end_time = time.time()
            duration = end_time - start_time
            course_id = getattr(self, 'course_id', '')
            tags = [
                u'handler_name:{}'.format(handler_name),
                u'action:handle',
                u'action_status:{}'.format(status),
                u'course_id:{}'.format(course_id),
                u'block_type:{}'.format(block.scope_ids.block_type),
                u'block_family:{}'.format(block.entry_point),
            ]
            dog_stats_api.increment(XMODULE_METRIC_NAME, tags=tags, sample_rate=XMODULE_METRIC_SAMPLE_RATE)
            dog_stats_api.histogram(
                XMODULE_DURATION_METRIC_NAME,
                duration,
                tags=tags,
                sample_rate=XMODULE_METRIC_SAMPLE_RATE
            )
            log.debug(
                "%.3fs - handle %s.%s (%s)",
                duration,
                block.__class__.__name__,
                handler_name,
                getattr(block, 'location', ''),
            )


class DescriptorSystem(MetricsMixin, ConfigurableFragmentWrapper, Runtime):
    """
    Base class for :class:`Runtime`s to be used with :class:`XModuleDescriptor`s
    """
    # pylint: disable=bad-continuation
    def __init__(
        self, load_item, resources_fs, error_tracker, get_policy=None, disabled_xblock_types=(), **kwargs
    ):
        """
        load_item: Takes a Location and returns an XModuleDescriptor

        resources_fs: A Filesystem object that contains all of the
            resources needed for the course

        error_tracker: A hook for tracking errors in loading the descriptor.
            Used for example to get a list of all non-fatal problems on course
            load, and display them to the user.

            A function of (error_msg). errortracker.py provides a
            handy make_error_tracker() function.

            Patterns for using the error handler:
               try:
                  x = access_some_resource()
                  check_some_format(x)
               except SomeProblem as err:
                  msg = 'Grommet {0} is broken: {1}'.format(x, str(err))
                  log.warning(msg)  # don't rely on tracker to log
                        # NOTE: we generally don't want content errors logged as errors
                  self.system.error_tracker(msg)
                  # work around
                  return 'Oops, couldn't load grommet'

               OR, if not in an exception context:

               if not check_something(thingy):
                  msg = "thingy {0} is broken".format(thingy)
                  log.critical(msg)
                  self.system.error_tracker(msg)

               NOTE: To avoid duplication, do not call the tracker on errors
               that you're about to re-raise---let the caller track them.

        get_policy: a function that takes a usage id and returns a dict of
            policy to apply.

        local_resource_url: an implementation of :meth:`xblock.runtime.Runtime.local_resource_url`

        """
        kwargs.setdefault('id_reader', OpaqueKeyReader())
        kwargs.setdefault('id_generator', AsideKeyGenerator())
        super(DescriptorSystem, self).__init__(**kwargs)

        # This is used by XModules to write out separate files during xml export
        self.export_fs = None

        self.load_item = load_item
        self.resources_fs = resources_fs
        self.error_tracker = error_tracker
        if get_policy:
            self.get_policy = get_policy
        else:
            self.get_policy = lambda u: {}

        self.disabled_xblock_types = disabled_xblock_types

    def get_block(self, usage_id, for_parent=None):
        """See documentation for `xblock.runtime:Runtime.get_block`"""
        return self.load_item(usage_id, for_parent=for_parent)

    def load_block_type(self, block_type):
        """
        Returns a subclass of :class:`.XBlock` that corresponds to the specified `block_type`.
        """
        if block_type in self.disabled_xblock_types:
            return self.default_class
        return super(DescriptorSystem, self).load_block_type(block_type)

    def get_field_provenance(self, xblock, field):
        """
        For the given xblock, return a dict for the field's current state:
        {
            'default_value': what json'd value will take effect if field is unset: either the field default or
            inherited value,
            'explicitly_set': boolean for whether the current value is set v default/inherited,
        }
        :param xblock:
        :param field:
        """
        # pylint: disable=protected-access
        # in runtime b/c runtime contains app-specific xblock behavior. Studio's the only app
        # which needs this level of introspection right now. runtime also is 'allowed' to know
        # about the kvs, dbmodel, etc.

        result = {}
        result['explicitly_set'] = xblock._field_data.has(xblock, field.name)
        try:
            result['default_value'] = xblock._field_data.default(xblock, field.name)
        except KeyError:
            result['default_value'] = field.to_json(field.default)
        return result

    def handler_url(self, block, handler_name, suffix='', query='', thirdparty=False):
        xmodule_runtime = getattr(block, 'xmodule_runtime', None)
        if xmodule_runtime is not None:
            return xmodule_runtime.handler_url(block, handler_name, suffix, query, thirdparty)
        else:
            # Currently, Modulestore is responsible for instantiating DescriptorSystems
            # This means that LMS/CMS don't have a way to define a subclass of DescriptorSystem
            # that implements the correct handler url. So, for now, instead, we will reference a
            # global function that the application can override.
            return descriptor_global_handler_url(block, handler_name, suffix, query, thirdparty)

    def local_resource_url(self, block, uri):
        """
        See :meth:`xblock.runtime.Runtime:local_resource_url` for documentation.
        """
        xmodule_runtime = getattr(block, 'xmodule_runtime', None)
        if xmodule_runtime is not None:
            return xmodule_runtime.local_resource_url(block, uri)
        else:
            # Currently, Modulestore is responsible for instantiating DescriptorSystems
            # This means that LMS/CMS don't have a way to define a subclass of DescriptorSystem
            # that implements the correct local_resource_url. So, for now, instead, we will reference a
            # global function that the application can override.
            return descriptor_global_local_resource_url(block, uri)

    def applicable_aside_types(self, block):
        """
        See :meth:`xblock.runtime.Runtime:applicable_aside_types` for documentation.
        """
        potential_set = set(super(DescriptorSystem, self).applicable_aside_types(block))
        if getattr(block, 'xmodule_runtime', None) is not None:
            if hasattr(block.xmodule_runtime, 'applicable_aside_types'):
                application_set = set(block.xmodule_runtime.applicable_aside_types(block))
                return list(potential_set.intersection(application_set))
        return list(potential_set)

    def resource_url(self, resource):
        """
        See :meth:`xblock.runtime.Runtime:resource_url` for documentation.
        """
        raise NotImplementedError("edX Platform doesn't currently implement XBlock resource urls")

    def publish(self, block, event_type, event):
        """
        See :meth:`xblock.runtime.Runtime:publish` for documentation.
        """
        xmodule_runtime = getattr(block, 'xmodule_runtime', None)
        if xmodule_runtime is not None:
            return xmodule_runtime.publish(block, event_type, event)

    def add_block_as_child_node(self, block, node):
        child = etree.SubElement(node, "unknown")
        child.set('url_name', block.url_name)
        block.add_xml_to_node(child)

    def publish(self, block, event_type, event):
        # A stub publish method that doesn't emit any events from XModuleDescriptors.
        pass

    def service(self, block, service_name):
        """
        Runtime-specific override for the XBlock service manager.  If a service is not currently
        instantiated and is declared as a critical requirement, an attempt is made to load the
        module.

        Arguments:
            block (an XBlock): this block's class will be examined for service
                decorators.
            service_name (string): the name of the service requested.

        Returns:
            An object implementing the requested service, or None.
        """
        # getting the service from parent module. making sure of block service declarations.
        service = super(DescriptorSystem, self).service(block=block, service_name=service_name)
        # Passing the block to service if it is callable e.g. ModuleI18nService. It is the responsibility of calling
        # service to handle the passing argument.
        if callable(service):
            return service(block)
        return service


new_contract('DescriptorSystem', DescriptorSystem)


class XMLParsingSystem(DescriptorSystem):
    def __init__(self, process_xml, **kwargs):
        """
        process_xml: Takes an xml string, and returns a XModuleDescriptor
            created from that xml
        """

        super(XMLParsingSystem, self).__init__(**kwargs)
        self.process_xml = process_xml

    def _usage_id_from_node(self, node, parent_id, id_generator=None):
        """Create a new usage id from an XML dom node.

        Args:
            node (lxml.etree.Element): The DOM node to interpret.
            parent_id: The usage ID of the parent block
            id_generator (IdGenerator): The :class:`.IdGenerator` to use
                for creating ids
        Returns:
            UsageKey: the usage key for the new xblock
        """
        return self.xblock_from_node(node, parent_id, id_generator).scope_ids.usage_id

    def xblock_from_node(self, node, parent_id, id_generator=None):
        """
        Create an XBlock instance from XML data.

        Args:
            xml_data (string): A string containing valid xml.
            system (XMLParsingSystem): The :class:`.XMLParsingSystem` used to connect the block
                to the outside world.
            id_generator (IdGenerator): An :class:`~xblock.runtime.IdGenerator` that
                will be used to construct the usage_id and definition_id for the block.

        Returns:
            XBlock: The fully instantiated :class:`~xblock.core.XBlock`.

        """
        id_generator = id_generator or self.id_generator
        # leave next line commented out - useful for low-level debugging
        # log.debug('[_usage_id_from_node] tag=%s, class=%s' % (node.tag, xblock_class))

        block_type = node.tag
        # remove xblock-family from elements
        node.attrib.pop('xblock-family', None)

        url_name = node.get('url_name')  # difference from XBlock.runtime
        def_id = id_generator.create_definition(block_type, url_name)
        usage_id = id_generator.create_usage(def_id)

        keys = ScopeIds(None, block_type, def_id, usage_id)
        block_class = self.mixologist.mix(self.load_block_type(block_type))

        aside_children = self.parse_asides(node, def_id, usage_id, id_generator)
        asides_tags = [x.tag for x in aside_children]

        block = block_class.parse_xml(node, self, keys, id_generator)
        self._convert_reference_fields_to_keys(block)  # difference from XBlock.runtime
        block.parent = parent_id
        block.save()

        asides = self.get_asides(block)
        for asd in asides:
            if asd.scope_ids.block_type in asides_tags:
                block.add_aside(asd)

        return block

    def parse_asides(self, node, def_id, usage_id, id_generator):
        """pull the asides out of the xml payload and instantiate them"""
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
        return aside_children

    def _make_usage_key(self, course_key, value):
        """
        Makes value into a UsageKey inside the specified course.
        If value is already a UsageKey, returns that.
        """
        if isinstance(value, UsageKey):
            return value
        return course_key.make_usage_key_from_deprecated_string(value)

    def _convert_reference_fields_to_keys(self, xblock):
        """
        Find all fields of type reference and convert the payload into UsageKeys
        """
        course_key = xblock.scope_ids.usage_id.course_key

        for field in xblock.fields.itervalues():
            if field.is_set_on(xblock):
                field_value = getattr(xblock, field.name)
                if field_value is None:
                    continue
                elif isinstance(field, Reference):
                    setattr(xblock, field.name, self._make_usage_key(course_key, field_value))
                elif isinstance(field, ReferenceList):
                    setattr(xblock, field.name, [self._make_usage_key(course_key, ele) for ele in field_value])
                elif isinstance(field, ReferenceValueDict):
                    for key, subvalue in field_value.iteritems():
                        assert isinstance(subvalue, basestring)
                        field_value[key] = self._make_usage_key(course_key, subvalue)
                    setattr(xblock, field.name, field_value)


class DiscussionService(object):
    """
    This is a temporary service that provides everything needed to render the discussion template.

    Used by xblock-discussion
    """

    def __init__(self, runtime):
        self.runtime = runtime

    def get_course_template_context(self):
        """
        Returns the context to render the course-level discussion templates.

        """
        # for some reason pylint reports courseware.access, courseware.courses and django_comment_client.forum.views
        # pylint: disable=import-error
        import json
        from django.conf import settings
        from django.http import HttpRequest
        import lms.lib.comment_client as cc
        from courseware.access import has_access
        from courseware.courses import get_course_with_access
        from django_comment_client.permissions import has_permission
        from django_comment_client.forum.views import get_threads, make_course_settings
        import django_comment_client.utils as utils
        from openedx.core.djangoapps.course_groups.cohorts import (
            is_course_cohorted,
            get_cohort_id,
            get_cohorted_commentables,
            get_course_cohorts
        )

        escapedict = {'"': '&quot;'}

        request = HttpRequest()
        user = self.runtime.user
        request.user = user
        user_info = cc.User.from_django_user(self.runtime.user).to_dict()
        course_id = self.runtime.course_id
        course = get_course_with_access(self.runtime.user, 'load_forum', course_id)
        user_cohort_id = get_cohort_id(user, course_id)

        unsafethreads, query_params = get_threads(request, course_id)
        threads = [utils.prepare_content(thread, course_id) for thread in unsafethreads]
        utils.add_courseware_context(threads, course, user)

        flag_moderator = has_permission(user, 'openclose_thread', course_id) or \
                         has_access(user, 'staff', course)

        annotated_content_info = utils.get_metadata_for_threads(course_id, threads, user, user_info)
        category_map = utils.get_discussion_category_map(course, user)

        cohorts = get_course_cohorts(course_id)
        cohorted_commentables = get_cohorted_commentables(course_id)

        course_settings = make_course_settings(course, user)

        context = {
            'user': user,
            'settings': settings,
            'course': course,
            'course_id': course_id,
            'staff_access': has_access(user, 'staff', course),
            'threads': saxutils.escape(json.dumps(threads), escapedict),
            'thread_pages': query_params['num_pages'],
            'user_info': saxutils.escape(json.dumps(user_info), escapedict),
            'flag_moderator': flag_moderator,
            'annotated_content_info': saxutils.escape(json.dumps(annotated_content_info), escapedict),
            'category_map': category_map,
            'roles': saxutils.escape(json.dumps(utils.get_role_ids(course_id)), escapedict),
            'is_moderator': has_permission(user, "see_all_cohorts", course_id),
            'cohorts': cohorts,
            'user_cohort': user_cohort_id,
            'sort_preference': user_info['default_sort_key'],
            'cohorted_commentables': cohorted_commentables,
            'is_course_cohorted': is_course_cohorted(course_id),
            'has_permission_to_create_thread': has_permission(user, "create_thread", course_id),
            'has_permission_to_create_comment': has_permission(user, "create_comment", course_id),
            'has_permission_to_create_subcomment': has_permission(user, "create_subcomment", course_id),
            'has_permission_to_openclose_thread': has_permission(user, "openclose_thread", course_id),
            'course_settings': saxutils.escape(json.dumps(course_settings), escapedict),
        }

        return context

    def get_inline_template_context(self):
        """
        Returns the context to render inline discussion templates.
        """
        # for some reason pylint reports courseware.access, courseware.courses and django_comment_client.forum.views
        # pylint: disable=import-error
        from django.conf import settings
        from courseware.courses import get_course_with_access
        from courseware.access import has_access
        from django_comment_client.permissions import has_permission
        from django_comment_client.utils import get_discussion_category_map

        course_id = self.runtime.course_id
        user = self.runtime.user

        course = get_course_with_access(user, 'load_forum', course_id)
        category_map = get_discussion_category_map(course, user)

        is_moderator = has_permission(user, "see_all_cohorts", course_id)
        flag_moderator =  has_permission(user, 'openclose_thread', course_id) or \
                          has_access(user, 'staff', course)

        context = {
            'user': user,
            'settings': settings,
            'course': course,
            'category_map': category_map,
            'is_moderator': is_moderator,
            'flag_moderator': flag_moderator,
            'has_permission_to_create_thread': has_permission(user, "create_thread", course_id),
            'has_permission_to_create_comment': has_permission(user, "create_comment", course_id),
            'has_permission_to_create_subcomment': has_permission(user, "create_subcomment", course_id),
            'has_permission_to_openclose_thread': has_permission(user, "openclose_thread", course_id)
        }

        return context


class ModuleSystem(MetricsMixin, ConfigurableFragmentWrapper, Runtime):
    """
    This is an abstraction such that x_modules can function independent
    of the courseware (e.g. import into other types of courseware, LMS,
    or if we want to have a sandbox server for user-contributed content)

    ModuleSystem objects are passed to x_modules to provide access to system
    functionality.

    Note that these functions can be closures over e.g. a django request
    and user, or other environment-specific info.
    """

    @contract(descriptor_runtime='DescriptorSystem')
    def __init__(
            self, static_url, track_function, get_module, render_template,
            replace_urls, descriptor_runtime, user=None, filestore=None,
            debug=False, hostname="", xqueue=None, publish=None, node_path="",
            anonymous_student_id='', course_id=None,
            cache=None, can_execute_unsafe_code=None, replace_course_urls=None,
            replace_jump_to_id_urls=None, error_descriptor_class=None, get_real_user=None,
            field_data=None, get_user_role=None, rebind_noauth_module_to_user=None,
            user_location=None, get_python_lib_zip=None, **kwargs):
        """
        Create a closure around the system environment.

        static_url - the base URL to static assets

        track_function - function of (event_type, event), intended for logging
                         or otherwise tracking the event.
                         TODO: Not used, and has inconsistent args in different
                         files.  Update or remove.

        get_module - function that takes a descriptor and returns a corresponding
                         module instance object.  If the current user does not have
                         access to that location, returns None.

        render_template - a function that takes (template_file, context), and
                         returns rendered html.

        user - The user to base the random number generator seed off of for this
                         request

        filestore - A filestore ojbect.  Defaults to an instance of OSFS based
                         at settings.DATA_DIR.

        xqueue - Dict containing XqueueInterface object, as well as parameters
                    for the specific StudentModule:
                    xqueue = {'interface': XQueueInterface object,
                              'callback_url': Callback into the LMS,
                              'queue_name': Target queuename in Xqueue}

        replace_urls - TEMPORARY - A function like static_replace.replace_urls
                         that capa_module can use to fix up the static urls in
                         ajax results.

        descriptor_runtime - A `DescriptorSystem` to use for loading xblocks by id

        anonymous_student_id - Used for tracking modules with student id

        course_id - the course_id containing this module

        publish(event) - A function that allows XModules to publish events (such as grade changes)

        cache - A cache object with two methods:
            .get(key) returns an object from the cache or None.
            .set(key, value, timeout_secs=None) stores a value in the cache with a timeout.

        can_execute_unsafe_code - A function returning a boolean, whether or
            not to allow the execution of unsafe, unsandboxed code.

        get_python_lib_zip - A function returning a bytestring or None.  The
            bytestring is the contents of a zip file that should be importable
            by other Python code running in the module.

        error_descriptor_class - The class to use to render XModules with errors

        get_real_user - function that takes `anonymous_student_id` and returns real user_id,
        associated with `anonymous_student_id`.

        get_user_role - A function that returns user role. Implementation is different
            for LMS and Studio.

        field_data - the `FieldData` to use for backing XBlock storage.

        rebind_noauth_module_to_user - rebinds module bound to AnonymousUser to a real user...used in LTI
           modules, which have an anonymous handler, to set legitimate users' data
        """

        # Add the DiscussionService for the LMS and Studio.
        services = kwargs.setdefault('services', {})
        services['discussion'] = DiscussionService(self)

        # Usage_store is unused, and field_data is often supplanted with an
        # explicit field_data during construct_xblock.
        kwargs.setdefault('id_reader', getattr(descriptor_runtime, 'id_reader', OpaqueKeyReader()))
        kwargs.setdefault('id_generator', getattr(descriptor_runtime, 'id_generator', AsideKeyGenerator()))
        super(ModuleSystem, self).__init__(field_data=field_data, **kwargs)

        self.STATIC_URL = static_url
        self.xqueue = xqueue
        self.track_function = track_function
        self.filestore = filestore
        self.get_module = get_module
        self.render_template = render_template
        self.DEBUG = self.debug = debug
        self.HOSTNAME = self.hostname = hostname
        self.seed = user.id if user is not None else 0
        self.replace_urls = replace_urls
        self.node_path = node_path
        self.anonymous_student_id = anonymous_student_id
        self.course_id = course_id
        self.user_is_staff = user is not None and user.is_staff

        if publish:
            self.publish = publish

        self.cache = cache or DoNothingCache()
        self.can_execute_unsafe_code = can_execute_unsafe_code or (lambda: False)
        self.get_python_lib_zip = get_python_lib_zip or (lambda: None)
        self.replace_course_urls = replace_course_urls
        self.replace_jump_to_id_urls = replace_jump_to_id_urls
        self.error_descriptor_class = error_descriptor_class
        self.xmodule_instance = None

        self.get_real_user = get_real_user
        self.user_location = user_location

        self.get_user_role = get_user_role
        self.descriptor_runtime = descriptor_runtime
        self.rebind_noauth_module_to_user = rebind_noauth_module_to_user

        if user:
            self.user_id = user.id

    def get(self, attr):
        """	provide uniform access to attributes (like etree)."""
        return self.__dict__.get(attr)

    def set(self, attr, val):
        """provide uniform access to attributes (like etree)"""
        self.__dict__[attr] = val

    def __repr__(self):
        kwargs = self.__dict__.copy()

        # Remove value set transiently by XBlock
        kwargs.pop('_view_name')

        return "{}{}".format(self.__class__.__name__, kwargs)

    @property
    def ajax_url(self):
        """
        The url prefix to be used by XModules to call into handle_ajax
        """
        assert self.xmodule_instance is not None
        return self.handler_url(self.xmodule_instance, 'xmodule_handler', '', '').rstrip('/?')

    def get_block(self, block_id, for_parent=None):
        return self.get_module(self.descriptor_runtime.get_block(block_id, for_parent=for_parent))

    def resource_url(self, resource):
        raise NotImplementedError("edX Platform doesn't currently implement XBlock resource urls")

    def publish(self, block, event_type, event):
        pass

    def service(self, block, service_name):
        """
        Runtime-specific override for the XBlock service manager.  If a service is not currently
        instantiated and is declared as a critical requirement, an attempt is made to load the
        module.

        Arguments:
            block (an XBlock): this block's class will be examined for service
                decorators.
            service_name (string): the name of the service requested.

        Returns:
            An object implementing the requested service, or None.
        """
        # getting the service from parent module. making sure of block service declarations.
        service = super(ModuleSystem, self).service(block=block, service_name=service_name)
        # Passing the block to service if it is callable e.g. ModuleI18nService. It is the responsibility of calling
        # service to handle the passing argument.
        if callable(service):
            return service(block)
        return service


class CombinedSystem(object):
    """
    This class is a shim to allow both pure XBlocks and XModuleDescriptors
    that have been bound as XModules to access both the attributes of ModuleSystem
    and of DescriptorSystem as a single runtime.
    """

    __slots__ = ('_module_system', '_descriptor_system')

    # This system doesn't override a number of methods that are provided by ModuleSystem and DescriptorSystem,
    # namely handler_url, local_resource_url, query, and resource_url.
    #
    # At runtime, the ModuleSystem and/or DescriptorSystem will define those methods
    #
    def __init__(self, module_system, descriptor_system):
        # These attributes are set directly to __dict__ below to avoid a recursion in getattr/setattr.
        self._module_system = module_system
        self._descriptor_system = descriptor_system

    def _get_student_block(self, block):
        """
        If block is an XModuleDescriptor that has been bound to a student, return
        the corresponding XModule, instead of the XModuleDescriptor.

        Otherwise, return block.
        """
        if isinstance(block, XModuleDescriptor) and block.xmodule_runtime:
            return block._xmodule  # pylint: disable=protected-access
        else:
            return block

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
        context = context or {}
        if view_name in PREVIEW_VIEWS:
            block = self._get_student_block(block)

        return self.__getattr__('render')(block, view_name, context)

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
            block (an XBlock): this block's class will be examined for service
                decorators.
            service_name (string): the name of the service requested.

        Returns:
            An object implementing the requested service, or None.

        """
        service = None

        if self._module_system:
            service = self._module_system.service(block, service_name)

        if service is None:
            service = self._descriptor_system.service(block, service_name)

        return service

    def __getattr__(self, name):
        """
        If the ModuleSystem doesn't have an attribute, try returning the same attribute from the
        DescriptorSystem, instead. This allows XModuleDescriptors that are bound as XModules
        to still function as XModuleDescriptors.
        """
        # First we try a lookup in the module system...
        try:
            return getattr(self._module_system, name)
        except AttributeError:
            return getattr(self._descriptor_system, name)

    def __setattr__(self, name, value):
        """
        If the ModuleSystem is set, set the attr on it.
        Always set the attr on the DescriptorSystem.
        """
        if name in self.__slots__:
            return super(CombinedSystem, self).__setattr__(name, value)

        if self._module_system:
            setattr(self._module_system, name, value)
        setattr(self._descriptor_system, name, value)

    def __delattr__(self, name):
        """
        If the ModuleSystem is set, delete the attribute from it.
        Always delete the attribute from the DescriptorSystem.
        """
        if self._module_system:
            delattr(self._module_system, name)
        delattr(self._descriptor_system, name)

    def __repr__(self):
        return "CombinedSystem({!r}, {!r})".format(self._module_system, self._descriptor_system)


class DoNothingCache(object):
    """A duck-compatible object to use in ModuleSystem when there's no cache."""
    def get(self, _key):
        return None

    def set(self, key, value, timeout=None):
        pass
