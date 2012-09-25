import logging
import pkg_resources
import yaml
import os

from functools import partial
from lxml import etree
from pprint import pprint
from collections import namedtuple
from pkg_resources import resource_listdir, resource_string, resource_isdir

from xmodule.modulestore import Location
from xmodule.timeparse import parse_time

log = logging.getLogger('mitx.' + __name__)


def dummy_track(event_type, event):
    pass


class ModuleMissingError(Exception):
    pass


class Plugin(object):
    """
    Base class for a system that uses entry_points to load plugins.

    Implementing classes are expected to have the following attributes:

        entry_point: The name of the entry point to load plugins from
    """

    _plugin_cache = None

    @classmethod
    def load_class(cls, identifier, default=None):
        """
        Loads a single class instance specified by identifier. If identifier
        specifies more than a single class, then logs a warning and returns the
        first class identified.

        If default is not None, will return default if no entry_point matching
        identifier is found. Otherwise, will raise a ModuleMissingError
        """
        if cls._plugin_cache is None:
            cls._plugin_cache = {}

        if identifier not in cls._plugin_cache:
            identifier = identifier.lower()
            classes = list(pkg_resources.iter_entry_points(
                    cls.entry_point, name=identifier))

            if len(classes) > 1:
                log.warning("Found multiple classes for {entry_point} with "
                            "identifier {id}: {classes}. "
                            "Returning the first one.".format(
                    entry_point=cls.entry_point,
                    id=identifier,
                    classes=", ".join(
                            class_.module_name for class_ in classes)))

            if len(classes) == 0:
                if default is not None:
                    return default
                raise ModuleMissingError(identifier)

            cls._plugin_cache[identifier] = classes[0].load()
        return cls._plugin_cache[identifier]

    @classmethod
    def load_classes(cls):
        """
        Returns a list of containing the identifiers and their corresponding classes for all
        of the available instances of this plugin
        """
        return [(class_.name, class_.load())
                for class_
                in pkg_resources.iter_entry_points(cls.entry_point)]


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


class XModule(HTMLSnippet):
    ''' Implements a generic learning module.

        Subclasses must at a minimum provide a definition for get_html in order
        to be displayed to users.

        See the HTML module for a simple example.
    '''

    # The default implementation of get_icon_class returns the icon_class
    # attribute of the class
    #
    # This attribute can be overridden by subclasses, and
    # the function can also be overridden if the icon class depends on the data
    # in the module
    icon_class = 'other'

    def __init__(self, system, location, definition, descriptor,
                 instance_state=None, shared_state=None, **kwargs):
        '''
        Construct a new xmodule

        system: A ModuleSystem allowing access to external resources

        location: Something Location-like that identifies this xmodule

        definition: A dictionary containing 'data' and 'children'. Both are
        optional

            'data': is JSON-like (string, dictionary, list, bool, or None,
                optionally nested).

                This defines all of the data necessary for a problem to display
                that is intrinsic to the problem.  It should not include any
                data that would vary between two courses using the same problem
                (due dates, grading policy, randomization, etc.)

            'children': is a list of Location-like values for child modules that
                this module depends on

        descriptor: the XModuleDescriptor that this module is an instance of.
            TODO (vshnayder): remove the definition parameter and location--they
            can come from the descriptor.

        instance_state: A string of serialized json that contains the state of
                this module for current student accessing the system, or None if
                no state has been saved

        shared_state: A string of serialized json that contains the state that
            is shared between this module and any modules of the same type with
            the same shared_state_key. This state is only shared per-student,
            not across different students

        kwargs: Optional arguments. Subclasses should always accept kwargs and
            pass them to the parent class constructor.

            Current known uses of kwargs:

                metadata: SCAFFOLDING - This dictionary will be split into
                    several different types of metadata in the future (course
                    policy, modification history, etc).  A dictionary containing
                    data that specifies information that is particular to a
                    problem in the context of a course
        '''
        self.system = system
        self.location = Location(location)
        self.definition = definition
        self.descriptor = descriptor
        self.instance_state = instance_state
        self.shared_state = shared_state
        self.id = self.location.url()
        self.url_name = self.location.name
        self.category = self.location.category
        self.metadata = kwargs.get('metadata', {})
        self._loaded_children = None

    @property
    def display_name(self):
        '''
        Return a display name for the module: use display_name if defined in
        metadata, otherwise convert the url name.
        '''
        return self.metadata.get('display_name',
                                 self.url_name.replace('_', ' '))

    def __unicode__(self):
        return '<x_module(id={0})>'.format(self.id)

    def get_children(self):
        '''
        Return module instances for all the children of this module.
        '''
        if self._loaded_children is None:
            child_locations = self.get_children_locations()
            children = [self.system.get_module(loc) for loc in child_locations]
            # get_module returns None if the current user doesn't have access
            # to the location.
            self._loaded_children = [c for c in children if c is not None]

        return self._loaded_children
    
    def get_children_locations(self):
        '''
        Returns the locations of each of child modules.
        
        Overriding this changes the behavior of get_children and
        anything that uses get_children, such as get_display_items.
        
        This method will not instantiate the modules of the children
        unless absolutely necessary, so it is cheaper to call than get_children
        
        These children will be the same children returned by the
        descriptor unless descriptor.has_dynamic_children() is true.
        '''
        return self.definition.get('children', [])

    def get_display_items(self):
        '''
        Returns a list of descendent module instances that will display
        immediately inside this module.
        '''
        items = []
        for child in self.get_children():
            items.extend(child.displayable_items())

        return items

    def displayable_items(self):
        '''
        Returns list of displayable modules contained by this module. If this
        module is visible, should return [self].
        '''
        return [self]

    def get_icon_class(self):
        '''
        Return a css class identifying this module in the context of an icon
        '''
        return self.icon_class

    ### Functions used in the LMS

    def get_instance_state(self):
        ''' State of the object, as stored in the database
        '''
        return '{}'

    def get_shared_state(self):
        '''
        Get state that should be shared with other instances
        using the same 'shared_state_key' attribute.
        '''
        return '{}'

    def get_score(self):
        ''' Score the student received on the problem.
        '''
        return None

    def max_score(self):
        ''' Maximum score. Two notes:

            * This is generic; in abstract, a problem could be 3/5 points on one
              randomization, and 5/7 on another

            * In practice, this is a Very Bad Idea, and (a) will break some code
              in place (although that code should get fixed), and (b) break some
              analytics we plan to put in place.
        '''
        return None

    def get_progress(self):
        ''' Return a progress.Progress object that represents how far the
        student has gone in this module.  Must be implemented to get correct
        progress tracking behavior in nesting modules like sequence and
        vertical.

        If this module has no notion of progress, return None.
        '''
        return None

    def handle_ajax(self, dispatch, get):
        ''' dispatch is last part of the URL.
            get is a dictionary-like object '''
        return ""


def policy_key(location):
    """
    Get the key for a location in a policy file.  (Since the policy file is
    specific to a course, it doesn't need the full location url).
    """
    return '{cat}/{name}'.format(cat=location.category, name=location.name)


Template = namedtuple("Template", "metadata data children")


class ResourceTemplates(object):
    @classmethod
    def templates(cls):
        """
        Returns a list of Template objects that describe possible templates that can be used
        to create a module of this type.
        If no templates are provided, there will be no way to create a module of
        this type

        Expects a class attribute template_dir_name that defines the directory
        inside the 'templates' resource directory to pull templates from
        """
        templates = []
        dirname = os.path.join('templates', cls.template_dir_name)
        if not resource_isdir(__name__, dirname):
            log.warning("No resource directory {dir} found when loading {cls_name} templates".format(
                dir=dirname,
                cls_name=cls.__name__,
            ))
            return []

        for template_file in resource_listdir(__name__, dirname):
            template_content = resource_string(__name__, os.path.join(dirname, template_file))
            template = yaml.load(template_content)
            templates.append(Template(**template))

        return templates


class XModuleDescriptor(Plugin, HTMLSnippet, ResourceTemplates):
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

    # Attributes for inpsection of the descriptor
    stores_state = False  # Indicates whether the xmodule state should be
    # stored in a database (independent of shared state)
    has_score = False  # This indicates whether the xmodule is a problem-type.
    # It should respond to max_score() and grade(). It can be graded or ungraded
    # (like a practice problem).

    # A list of metadata that this module can inherit from its parent module
    inheritable_metadata = (
        'graded', 'start', 'due', 'graceperiod', 'showanswer', 'rerandomize',
        # TODO (ichuang): used for Fall 2012 xqa server access
        'xqa_key',
        # TODO: This is used by the XMLModuleStore to provide for locations for
        # static files, and will need to be removed when that code is removed
        'data_dir'
    )

    # cdodge: this is a list of metadata names which are 'system' metadata
    # and should not be edited by an end-user
    system_metadata_fields = [ 'data_dir' ]
    
    # A list of descriptor attributes that must be equal for the descriptors to
    # be equal
    equality_attributes = ('definition', 'metadata', 'location',
                           'shared_state_key', '_inherited_metadata')

    # Name of resource directory to load templates from
    template_dir_name = "default"

    # ============================= STRUCTURAL MANIPULATION ===================
    def __init__(self,
                 system,
                 definition=None,
                 **kwargs):
        """
        Construct a new XModuleDescriptor. The only required arguments are the
        system, used for interaction with external resources, and the
        definition, which specifies all the data needed to edit and display the
        problem (but none of the associated metadata that handles recordkeeping
        around the problem).

        This allows for maximal flexibility to add to the interface while
        preserving backwards compatibility.

        system: A DescriptorSystem for interacting with external resources

        definition: A dict containing `data` and `children` representing the
        problem definition

        Current arguments passed in kwargs:

            location: A xmodule.modulestore.Location object indicating the name
                and ownership of this problem

            shared_state_key: The key to use for sharing StudentModules with
                other modules of this type

            metadata: A dictionary containing the following optional keys:
                goals: A list of strings of learning goals associated with this
                    module
                display_name: The name to use for displaying this module to the
                    user
                url_name: The name to use for this module in urls and other places
                    where a unique name is needed.
                format: The format of this module ('Homework', 'Lab', etc)
                graded (bool): Whether this module is should be graded or not
                start (string): The date for which this module will be available
                due (string): The due date for this module
                graceperiod (string): The amount of grace period to allow when
                    enforcing the due date
                showanswer (string): When to show answers for this module
                rerandomize (string): When to generate a newly randomized
                    instance of the module data
        """
        self.system = system
        self.metadata = kwargs.get('metadata', {})
        self.definition = definition if definition is not None else {}
        self.location = Location(kwargs.get('location'))
        self.url_name = self.location.name
        self.category = self.location.category
        self.shared_state_key = kwargs.get('shared_state_key')

        self._child_instances = None
        self._inherited_metadata = set()

    @property
    def display_name(self):
        '''
        Return a display name for the module: use display_name if defined in
        metadata, otherwise convert the url name.
        '''
        return self.metadata.get('display_name',
                                 self.url_name.replace('_', ' '))

    @property
    def start(self):
        """
        If self.metadata contains start, return it.  Else return None.
        """
        if 'start' not in self.metadata:
            return None
        return self._try_parse_time('start')

    @property
    def own_metadata(self):
        """
        Return the metadata that is not inherited, but was defined on this module.
        """
        return dict((k, v) for k, v in self.metadata.items()
                    if k not in self._inherited_metadata)

    @staticmethod
    def compute_inherited_metadata(node):
        """Given a descriptor, traverse all of its descendants and do metadata
        inheritance.  Should be called on a CourseDescriptor after importing a
        course.

        NOTE: This means that there is no such thing as lazy loading at the
        moment--this accesses all the children."""
        for c in node.get_children():
            c.inherit_metadata(node.metadata)
            XModuleDescriptor.compute_inherited_metadata(c)

    def inherit_metadata(self, metadata):
        """
        Updates this module with metadata inherited from a containing module.
        Only metadata specified in self.inheritable_metadata will
        be inherited
        """
        # Set all inheritable metadata from kwargs that are
        # in self.inheritable_metadata and aren't already set in metadata
        for attr in self.inheritable_metadata:
            if attr not in self.metadata and attr in metadata:
                self._inherited_metadata.add(attr)
                self.metadata[attr] = metadata[attr]

    def get_children(self):
        """Returns a list of XModuleDescriptor instances for the children of
        this module"""
        if self._child_instances is None:
            self._child_instances = []
            for child_loc in self.definition.get('children', []):
                child = self.system.load_item(child_loc)
                # TODO (vshnayder): this should go away once we have
                # proper inheritance support in mongo.  The xml
                # datastore does all inheritance on course load.
                child.inherit_metadata(self.metadata)
                self._child_instances.append(child)

        return self._child_instances

    def get_child_by_url_name(self, url_name):
        """
        Return a child XModuleDescriptor with the specified url_name, if it exists, and None otherwise.
        """
        for c in self.get_children():
            if c.url_name == url_name:
                return c
        return None

    def xmodule_constructor(self, system):
        """
        Returns a constructor for an XModule. This constructor takes two
        arguments: instance_state and shared_state, and returns a fully
        instantiated XModule
        """
        return partial(
            self.module_class,
            system,
            self.location,
            self.definition,
            self,
            metadata=self.metadata
        )
    
    
    def has_dynamic_children(self):
        """
        Returns True if this descriptor has dynamic children for a given
        student when the module is created.
        
        Returns False if the children of this descriptor are the same
        children that the module will return for any student. 
        """
        return False
        

    # ================================= JSON PARSING ===========================
    @staticmethod
    def load_from_json(json_data, system, default_class=None):
        """
        This method instantiates the correct subclass of XModuleDescriptor based
        on the contents of json_data.

        json_data must contain a 'location' element, and must be suitable to be
        passed into the subclasses `from_json` method.
        """
        class_ = XModuleDescriptor.load_class(
            json_data['location']['category'],
            default_class
        )
        return class_.from_json(json_data, system)

    @classmethod
    def from_json(cls, json_data, system):
        """
        Creates an instance of this descriptor from the supplied json_data.
        This may be overridden by subclasses

        json_data: A json object specifying the definition and any optional
            keyword arguments for the XModuleDescriptor

        system: A DescriptorSystem for interacting with external resources
        """
        return cls(system=system, **json_data)

    # ================================= XML PARSING ============================
    @staticmethod
    def load_from_xml(xml_data,
            system,
            org=None,
            course=None,
            default_class=None):
        """
        This method instantiates the correct subclass of XModuleDescriptor based
        on the contents of xml_data.

        xml_data must be a string containing valid xml

        system is an XMLParsingSystem

        org and course are optional strings that will be used in the generated
            module's url identifiers
        """
        class_ = XModuleDescriptor.load_class(
            etree.fromstring(xml_data).tag,
            default_class
            )
        # leave next line, commented out - useful for low-level debugging
        # log.debug('[XModuleDescriptor.load_from_xml] tag=%s, class_=%s' % (
        #        etree.fromstring(xml_data).tag,class_))

        return class_.from_xml(xml_data, system, org, course)

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses

        xml_data: A string of xml that will be translated into data and children
            for this module

        system is an XMLParsingSystem

        org and course are optional strings that will be used in the generated
            module's url identifiers
        """
        raise NotImplementedError(
            'Modules must implement from_xml to be parsable from xml')

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
        """
        raise NotImplementedError(
            'Modules must implement export_to_xml to enable xml export')

    # =============================== Testing ==================================
    def get_sample_state(self):
        """
        Return a list of tuples of instance_state, shared_state. Each tuple
        defines a sample case for this module
        """
        return [('{}', '{}')]

    # =============================== BUILTIN METHODS ==========================
    def __eq__(self, other):
        eq = (self.__class__ == other.__class__ and
                all(getattr(self, attr, None) == getattr(other, attr, None)
                    for attr in self.equality_attributes))

        if not eq:
            for attr in self.equality_attributes:
                pprint((getattr(self, attr, None),
                       getattr(other, attr, None),
                       getattr(self, attr, None) == getattr(other, attr, None)))

        return eq

    def __repr__(self):
        return ("{class_}({system!r}, {definition!r}, location={location!r},"
                " metadata={metadata!r})".format(
            class_=self.__class__.__name__,
            system=self.system,
            definition=self.definition,
            location=self.location,
            metadata=self.metadata
        ))

    # ================================ Internal helpers =======================

    def _try_parse_time(self, key):
        """
        Parse an optional metadata key containing a time: if present, complain
        if it doesn't parse.
        Return None if not present or invalid.
        """
        if key in self.metadata:
            try:
                return parse_time(self.metadata[key])
            except ValueError as e:
                msg = "Descriptor {0} loaded with a bad metadata key '{1}': '{2}'".format(
                    self.location.url(), self.metadata[key], e)
                log.warning(msg)
        return None


class DescriptorSystem(object):
    def __init__(self, load_item, resources_fs, error_tracker, **kwargs):
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
        """

        self.load_item = load_item
        self.resources_fs = resources_fs
        self.error_tracker = error_tracker


class XMLParsingSystem(DescriptorSystem):
    def __init__(self, load_item, resources_fs, error_tracker, process_xml, policy, **kwargs):
        """
        load_item, resources_fs, error_tracker: see DescriptorSystem

        policy: a policy dictionary for overriding xml metadata

        process_xml: Takes an xml string, and returns a XModuleDescriptor
            created from that xml
        """
        DescriptorSystem.__init__(self, load_item, resources_fs, error_tracker,
                                  **kwargs)
        self.process_xml = process_xml
        self.policy = policy


class ModuleSystem(object):
    '''
    This is an abstraction such that x_modules can function independent
    of the courseware (e.g. import into other types of courseware, LMS,
    or if we want to have a sandbox server for user-contributed content)

    ModuleSystem objects are passed to x_modules to provide access to system
    functionality.

    Note that these functions can be closures over e.g. a django request
    and user, or other environment-specific info.
    '''
    def __init__(self,
                 ajax_url,
                 track_function,
                 get_module,
                 render_template,
                 replace_urls,
                 user=None,
                 filestore=None,
                 debug=False,
                 xqueue=None,
                 node_path="",
                 anonymous_student_id=''):
        '''
        Create a closure around the system environment.

        ajax_url - the url where ajax calls to the encapsulating module go.

        track_function - function of (event_type, event), intended for logging
                         or otherwise tracking the event.
                         TODO: Not used, and has inconsistent args in different
                         files.  Update or remove.

        get_module - function that takes (location) and returns a corresponding
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

        anonymous_student_id - Used for tracking modules with student id
        '''
        self.ajax_url = ajax_url
        self.xqueue = xqueue
        self.track_function = track_function
        self.filestore = filestore
        self.get_module = get_module
        self.render_template = render_template
        self.DEBUG = self.debug = debug
        self.seed = user.id if user is not None else 0
        self.replace_urls = replace_urls
        self.node_path = node_path
        self.anonymous_student_id = anonymous_student_id
        self.user_is_staff = user is not None and user.is_staff

    def get(self, attr):
        '''	provide uniform access to attributes (like etree).'''
        return self.__dict__.get(attr)

    def set(self, attr, val):
        '''provide uniform access to attributes (like etree)'''
        self.__dict__[attr] = val

    def __repr__(self):
        return repr(self.__dict__)

    def __str__(self):
        return str(self.__dict__)
