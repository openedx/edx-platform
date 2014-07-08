import logging
import os
import sys
import yaml

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

from xblock.core import XBlock
from xblock.fields import Scope, Integer, Float, List, XBlockMixin, String, Dict
from xblock.fragment import Fragment
from xblock.runtime import Runtime, IdReader
from xmodule.fields import RelativeTime

from xmodule.errortracker import exc_info_to_str
from xmodule.modulestore.exceptions import ItemNotFoundError
from opaque_keys.edx.keys import UsageKey
from xmodule.exceptions import UndefinedContext
from dogapi import dog_stats_api


log = logging.getLogger(__name__)

XMODULE_METRIC_NAME = 'edxapp.xmodule'

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
        return usage_id.definition_key

    def get_block_type(self, def_id):
        """Retrieve the block_type of a particular definition

        Args:
            def_id: The id of the definition to query

        Returns:
            The `block_type` of the definition
        """
        return def_id.block_type


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

        fragment = resource_string(__name__, 'js/src/xmodule.js')

        if fragment not in js:
            js.insert(0, fragment)

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


def shim_xmodule_js(fragment):
    """
    Set up the XBlock -> XModule shim on the supplied :class:`xblock.fragment.Fragment`
    """
    if not fragment.js_init_fn:
        fragment.initialize_js('XBlockToXModuleShim')


class XModuleMixin(XBlockMixin):
    """
    Fields and methods used by XModules internally.

    Adding this Mixin to an :class:`XBlock` allows it to cooperate with old-style :class:`XModules`
    """

    # Attributes for inspection of the descriptor

    # This indicates whether the xmodule is a problem-type.
    # It should respond to max_score() and grade(). It can be graded or ungraded
    # (like a practice problem).
    has_score = False

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

    display_name = String(
        display_name="Display Name",
        help="This name appears in the horizontal navigation at the top of the page.",
        scope=Scope.settings,
        # it'd be nice to have a useful default but it screws up other things; so,
        # use display_name_with_default for those
        default=None
    )

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
        return self.location.name

    @property
    def display_name_with_default(self):
        """
        Return a display name for the module: use display_name if defined in
        metadata, otherwise convert the url name.
        """
        name = self.display_name
        if name is None:
            name = self.url_name.replace('_', ' ')
        return name

    @property
    def xblock_kvs(self):
        """
        Retrieves the internal KeyValueStore for this XModule.

        Should only be used by the persistence layer. Use with caution.
        """
        # if caller wants kvs, caller's assuming it's up to date; so, decache it
        self.save()
        return self._field_data._kvs  # pylint: disable=protected-access

    def get_explicitly_set_fields_by_scope(self, scope=Scope.content):
        """
        Get a dictionary of the fields for the given scope which are set explicitly on this xblock. (Including
        any set to None.)
        """
        result = {}
        for field in self.fields.values():
            if (field.scope == scope and field.is_set_on(self)):
                result[field.name] = field.read_json(self)
        return result

    def has_children_at_depth(self, depth):
        """
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
        """
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
            return [self.display_name_with_default]

    def get_children(self):
        """Returns a list of XBlock instances for the children of
        this module"""

        if not self.has_children:
            return []

        if getattr(self, '_child_instances', None) is None:
            self._child_instances = []  # pylint: disable=attribute-defined-outside-init
            for child_loc in self.children:
                try:
                    child = self.runtime.get_block(child_loc)
                    child.runtime.export_fs = self.runtime.export_fs
                except ItemNotFoundError:
                    log.exception(u'Unable to load item {loc}, skipping'.format(loc=child_loc))
                    continue
                self._child_instances.append(child)

        return self._child_instances

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

    def bind_for_student(self, xmodule_runtime, field_data):
        """
        Set up this XBlock to act as an XModule instead of an XModuleDescriptor.

        :param xmodule_runtime: the runtime to use when accessing student facing methods
        :type xmodule_runtime: :class:`ModuleSystem`
        :param field_data: The :class:`FieldData` to use for all subsequent data access
        :type field_data: :class:`FieldData`
        """
        # pylint: disable=attribute-defined-outside-init
        self.xmodule_runtime = xmodule_runtime
        self._field_data = field_data


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
class XModule(XModuleMixin, HTMLSnippet, XBlock):  # pylint: disable=abstract-method
    """ Implements a generic learning module.

        Subclasses must at a minimum provide a definition for get_html in order
        to be displayed to users.

        See the HTML module for a simple example.
    """

    has_score = descriptor_attr('has_score')
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
        super(XModule, self).__init__(*args, **kwargs)
        self._loaded_children = None
        self.runtime.xmodule_instance = self

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

    def get_children(self):
        """
        Return module instances for all the children of this module.
        """
        if self._loaded_children is None:
            child_descriptors = self.get_child_descriptors()

            # This deliberately uses system.get_module, rather than runtime.get_block,
            # because we're looking at XModule children, rather than XModuleDescriptor children.
            # That means it can use the deprecated XModule apis, rather than future XBlock apis

            # TODO: Once we're in a system where this returns a mix of XModuleDescriptors
            # and XBlocks, we're likely to have to change this more
            children = [self.system.get_module(descriptor) for descriptor in child_descriptors]
            # get_module returns None if the current user doesn't have access
            # to the location.
            self._loaded_children = [c for c in children if c is not None]

        return self._loaded_children

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
class XModuleDescriptor(XModuleMixin, HTMLSnippet, ResourceTemplates, XBlock):
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
        self.edited_by = self.edited_on = self.previous_version = self.update_version = self.definition_locator = None
        self.xmodule_runtime = None

    @classmethod
    def _translate(cls, key):
        'VS[compat]'
        return cls.metadata_translations.get(key, key)

    # ================================= XML PARSING ============================
    @classmethod
    def parse_xml(cls, node, runtime, keys, id_generator):
        """
        Interpret the parsed XML in `node`, creating an XModuleDescriptor.
        """
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
        return (self.scope_ids == other.scope_ids and
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

            if field.scope != Scope.settings or field in self.non_editable_metadata_fields:
                continue

            metadata_fields[field.name] = self._create_metadata_editor_info(field)

        return metadata_fields

    def _create_metadata_editor_info(self, field):
        """
        Creates the information needed by the metadata editor for a specific field.
        """
        def jsonify_value(field, json_choice):
            if isinstance(json_choice, dict):
                json_choice = dict(json_choice)  # make a copy so below doesn't change the original
                if 'display_name' in json_choice:
                    json_choice['display_name'] = get_text(json_choice['display_name'])
                if 'value' in json_choice:
                    json_choice['value'] = field.to_json(json_choice['value'])
            else:
                json_choice = field.to_json(json_choice)
            return json_choice

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
        metadata_field_editor_info['type'] = editor_type
        metadata_field_editor_info['options'] = [] if values is None else values

        return metadata_field_editor_info

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


class ConfigurableFragmentWrapper(object):  # pylint: disable=abstract-method
    """
    Runtime mixin that allows for composition of many `wrap_child` wrappers
    """
    def __init__(self, wrappers=None, **kwargs):
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

    def wrap_child(self, block, view, frag, context):
        """
        See :func:`Runtime.wrap_child`
        """
        for wrapper in self.wrappers:
            frag = wrapper(block, view, frag, context)

        return frag


# This function exists to give applications (LMS/CMS) a place to monkey-patch until
# we can refactor modulestore to split out the FieldData half of its interface from
# the Runtime part of its interface. This function matches the Runtime.handler_url interface
def descriptor_global_handler_url(block, handler_name, suffix='', query='', thirdparty=False):  # pylint: disable=invalid-name, unused-argument
    """
    See :meth:`xblock.runtime.Runtime.handler_url`.
    """
    raise NotImplementedError("Applications must monkey-patch this function before using handler_url for studio_view")


# This function exists to give applications (LMS/CMS) a place to monkey-patch until
# we can refactor modulestore to split out the FieldData half of its interface from
# the Runtime part of its interface. This function matches the Runtime.local_resource_url interface
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
        try:
            status = "success"
            return super(MetricsMixin, self).render(block, view_name, context=context)

        except:
            status = "failure"
            raise

        finally:
            course_id = getattr(self, 'course_id', '')
            dog_stats_api.increment(XMODULE_METRIC_NAME, tags=[
                u'view_name:{}'.format(view_name),
                u'action:render',
                u'action_status:{}'.format(status),
                u'course_id:{}'.format(course_id),
                u'block_type:{}'.format(block.scope_ids.block_type)
            ])

    def handle(self, block, handler_name, request, suffix=''):
        handle = None
        try:
            status = "success"
            return super(MetricsMixin, self).handle(block, handler_name, request, suffix=suffix)

        except:
            status = "failure"
            raise

        finally:
            course_id = getattr(self, 'course_id', '')
            dog_stats_api.increment(XMODULE_METRIC_NAME, tags=[
                u'handler_name:{}'.format(handler_name),
                u'action:handle',
                u'action_status:{}'.format(status),
                u'course_id:{}'.format(course_id),
                u'block_type:{}'.format(block.scope_ids.block_type)
            ])


class DescriptorSystem(MetricsMixin, ConfigurableFragmentWrapper, Runtime):  # pylint: disable=abstract-method
    """
    Base class for :class:`Runtime`s to be used with :class:`XModuleDescriptor`s
    """

    def __init__(
        self, load_item, resources_fs, error_tracker, get_policy=None, **kwargs
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
        super(DescriptorSystem, self).__init__(id_reader=OpaqueKeyReader(), **kwargs)

        # This is used by XModules to write out separate files during xml export
        self.export_fs = None

        self.load_item = load_item
        self.resources_fs = resources_fs
        self.error_tracker = error_tracker
        if get_policy:
            self.get_policy = get_policy
        else:
            self.get_policy = lambda u: {}

    def get_block(self, usage_id):
        """See documentation for `xblock.runtime:Runtime.get_block`"""
        return self.load_item(usage_id)

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
        # in runtime b/c runtime contains app-specific xblock behavior. Studio's the only app
        # which needs this level of introspection right now. runtime also is 'allowed' to know
        # about the kvs, dbmodel, etc.

        result = {}
        result['explicitly_set'] = xblock._field_data.has(xblock, field.name)
        try:
            block_inherited = xblock.xblock_kvs.inherited_settings
        except AttributeError:  # if inherited_settings doesn't exist on kvs
            block_inherited = {}
        if field.name in block_inherited:
            result['default_value'] = block_inherited[field.name]
        else:
            result['default_value'] = field.to_json(field.default)
        return result

    def render(self, block, view_name, context=None):
        if view_name in PREVIEW_VIEWS:
            assert block.xmodule_runtime is not None
            if isinstance(block, (XModule, XModuleDescriptor)):
                to_render = block._xmodule
            else:
                to_render = block
            return block.xmodule_runtime.render(to_render, view_name, context)
        else:
            return super(DescriptorSystem, self).render(block, view_name, context)

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


class XMLParsingSystem(DescriptorSystem):
    def __init__(self, process_xml, **kwargs):
        """
        process_xml: Takes an xml string, and returns a XModuleDescriptor
            created from that xml
        """

        super(XMLParsingSystem, self).__init__(**kwargs)
        self.process_xml = process_xml


class ModuleSystem(MetricsMixin, ConfigurableFragmentWrapper, Runtime):  # pylint: disable=abstract-method
    """
    This is an abstraction such that x_modules can function independent
    of the courseware (e.g. import into other types of courseware, LMS,
    or if we want to have a sandbox server for user-contributed content)

    ModuleSystem objects are passed to x_modules to provide access to system
    functionality.

    Note that these functions can be closures over e.g. a django request
    and user, or other environment-specific info.
    """
    def __init__(
            self, static_url, track_function, get_module, render_template,
            replace_urls, descriptor_runtime, user=None, filestore=None,
            debug=False, hostname="", xqueue=None, publish=None, node_path="",
            anonymous_student_id='', course_id=None,
            open_ended_grading_interface=None, s3_interface=None,
            cache=None, can_execute_unsafe_code=None, replace_course_urls=None,
            replace_jump_to_id_urls=None, error_descriptor_class=None, get_real_user=None,
            field_data=None, get_user_role=None, rebind_noauth_module_to_user=None,
            user_location=None, **kwargs):
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

        error_descriptor_class - The class to use to render XModules with errors

        get_real_user - function that takes `anonymous_student_id` and returns real user_id,
        associated with `anonymous_student_id`.

        get_user_role - A function that returns user role. Implementation is different
            for LMS and Studio.

        field_data - the `FieldData` to use for backing XBlock storage.

        rebind_noauth_module_to_user - rebinds module bound to AnonymousUser to a real user...used in LTI
           modules, which have an anonymous handler, to set legitimate users' data
        """

        # Usage_store is unused, and field_data is often supplanted with an
        # explicit field_data during construct_xblock.
        super(ModuleSystem, self).__init__(id_reader=OpaqueKeyReader(), field_data=field_data, **kwargs)

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

        self.open_ended_grading_interface = open_ended_grading_interface
        self.s3_interface = s3_interface

        self.cache = cache or DoNothingCache()
        self.can_execute_unsafe_code = can_execute_unsafe_code or (lambda: False)
        self.replace_course_urls = replace_course_urls
        self.replace_jump_to_id_urls = replace_jump_to_id_urls
        self.error_descriptor_class = error_descriptor_class
        self.xmodule_instance = None

        self.get_real_user = get_real_user
        self.user_location = user_location

        self.get_user_role = get_user_role
        self.descriptor_runtime = descriptor_runtime
        self.rebind_noauth_module_to_user = rebind_noauth_module_to_user

    def get(self, attr):
        """	provide uniform access to attributes (like etree)."""
        return self.__dict__.get(attr)

    def set(self, attr, val):
        """provide uniform access to attributes (like etree)"""
        self.__dict__[attr] = val

    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    @property
    def ajax_url(self):
        """
        The url prefix to be used by XModules to call into handle_ajax
        """
        assert self.xmodule_instance is not None
        return self.handler_url(self.xmodule_instance, 'xmodule_handler', '', '').rstrip('/?')

    def get_block(self, block_id):
        return self.get_module(self.descriptor_runtime.get_block(block_id))

    def resource_url(self, resource):
        raise NotImplementedError("edX Platform doesn't currently implement XBlock resource urls")

    def publish(self, block, event_type, event):
        pass


class DoNothingCache(object):
    """A duck-compatible object to use in ModuleSystem when there's no cache."""
    def get(self, _key):
        return None

    def set(self, key, value, timeout=None):
        pass
