from lxml import etree
import pkg_resources
import logging

from keystore import Location
from functools import partial

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
    @classmethod
    def load_class(cls, identifier, default=None):
        """
        Loads a single class intance specified by identifier. If identifier
        specifies more than a single class, then logs a warning and returns the first
        class identified.

        If default is not None, will return default if no entry_point matching identifier
        is found. Otherwise, will raise a ModuleMissingError
        """
        identifier = identifier.lower()
        classes = list(pkg_resources.iter_entry_points(cls.entry_point, name=identifier))
        if len(classes) > 1:
            log.warning("Found multiple classes for {entry_point} with identifier {id}: {classes}. Returning the first one.".format(
                entry_point=cls.entry_point,
                id=identifier,
                classes=", ".join(class_.module_name for class_ in classes)))

        if len(classes) == 0:
            if default is not None:
                return default
            raise ModuleMissingError(identifier)

        return classes[0].load()

    @classmethod
    def load_classes(cls):
        return [class_.load()
                for class_
                in pkg_resources.iter_entry_points(cls.entry_point)]


class XModule(object):
    ''' Implements a generic learning module. 
        Initialized on access with __init__, first time with instance_state=None, and
        shared_state=None. In later instantiations, instance_state will not be None,
        but shared_state may be

        See the HTML module for a simple example
    '''
    icon_class = 'other'

    def __init__(self, system, location, definition, instance_state=None, shared_state=None, **kwargs):
        '''
        Construct a new xmodule

        system: An I4xSystem allowing access to external resources
        location: Something Location-like that identifies this xmodule
        definition: A dictionary containing 'data' and 'children'. Both are optional
            'data': is a json object specifying the behavior of this xmodule
            'children': is a list of xmodule urls for child modules that this module depends on
        '''
        self.system = system
        self.location = Location(location)
        self.definition = definition
        self.instance_state = instance_state
        self.shared_state = shared_state
        self.id = self.location.url()
        self.name = self.location.name
        self.type = self.location.category
        self.metadata = kwargs.get('metadata', {})
        self._loaded_children = None

    def get_name(self):
        name = self.__xmltree.get('name')
        if name:
            return name
        else:
            raise "We should iterate through children and find a default name"

    def get_children(self):
        '''
        Return module instances for all the children of this module.
        '''
        if self._loaded_children is None:
            self._loaded_children = [self.system.get_module(child) for child in self.definition.get('children', [])]
        return self._loaded_children

    def get_display_items(self):
        '''
        Returns a list of descendent module instances that will display immediately
        inside this module
        '''
        items = []
        for child in self.get_children():
            items.extend(child.displayable_items())

        return items

    def displayable_items(self):
        '''
        Returns list of displayable modules contained by this module. If this module
        is visible, should return [self]
        '''
        return [self]

    def get_icon_class(self):
        '''
        Return a class identifying this module in the context of an icon
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
            * This is generic; in abstract, a problem could be 3/5 points on one randomization, and 5/7 on another
            * In practice, this is a Very Bad Idea, and (a) will break some code in place (although that code
              should get fixed), and (b) break some analytics we plan to put in place. 
        ''' 
        return None

    def get_html(self):
        ''' HTML, as shown in the browser. This is the only method that must be implemented
        '''
        return "Unimplemented"

    def get_progress(self):
        ''' Return a progress.Progress object that represents how far the student has gone
        in this module.  Must be implemented to get correct progress tracking behavior in
        nesting modules like sequence and vertical.

        If this module has no notion of progress, return None.
        '''
        return None

    def handle_ajax(self, dispatch, get):
        ''' dispatch is last part of the URL. 
            get is a dictionary-like object ''' 
        return ""


class XModuleDescriptor(Plugin):
    """
    An XModuleDescriptor is a specification for an element of a course. This could
    be a problem, an organizational element (a group of content), or a segment of video,
    for example.

    XModuleDescriptors are independent and agnostic to the current student state on a
    problem. They handle the editing interface used by instructors to create a problem,
    and can generate XModules (which do know about student state).
    """
    entry_point = "xmodule.v1"
    js = {}
    js_module = None

    # A list of metadata that this module can inherit from its parent module
    inheritable_metadata = ('graded', 'due', 'graceperiod', 'showanswer', 'rerandomize')

    def __init__(self,
                 system,
                 definition=None,
                 **kwargs):
        """
        Construct a new XModuleDescriptor. The only required arguments are the
        system, used for interaction with external resources, and the definition,
        which specifies all the data needed to edit and display the problem (but none
        of the associated metadata that handles recordkeeping around the problem).

        This allows for maximal flexibility to add to the interface while preserving
        backwards compatibility.

        system: An XModuleSystem for interacting with external resources
        definition: A dict containing `data` and `children` representing the problem definition

        Current arguments passed in kwargs:
            location: A keystore.Location object indicating the name and ownership of this problem
            shared_state_key: The key to use for sharing StudentModules with other
                modules of this type
            metadata: A dictionary containing the following optional keys:
                goals: A list of strings of learning goals associated with this module
                display_name: The name to use for displaying this module to the user
                format: The format of this module ('Homework', 'Lab', etc)
                graded (bool): Whether this module is should be graded or not
                due (string): The due date for this module
                graceperiod (string): The amount of grace period to allow when enforcing the due date
                showanswer (string): When to show answers for this module
                rerandomize (string): When to generate a newly randomized instance of the module data
        """
        self.system = system
        self.definition = definition if definition is not None else {}
        self.name = Location(kwargs.get('location')).name
        self.type = Location(kwargs.get('location')).category
        self.url = Location(kwargs.get('location')).url()
        self.metadata = kwargs.get('metadata', {})
        self.shared_state_key = kwargs.get('shared_state_key')

        self._child_instances = None

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

        json_data: Json data specifying the data, children, and metadata for the descriptor
        system: An XModuleSystem for interacting with external resources
        """
        return cls(system=system, **json_data)

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
        org and course are optional strings that will be used in the generated modules
            url identifiers
        """
        class_ = XModuleDescriptor.load_class(
            etree.fromstring(xml_data).tag,
            default_class
        )
        return class_.from_xml(xml_data, system, org, course)

    @classmethod
    def from_xml(cls, xml_data, system, org=None, course=None):
        """
        Creates an instance of this descriptor from the supplied xml_data.
        This may be overridden by subclasses

        xml_data: A string of xml that will be translated into data and children for
            this module
        system is an XMLParsingSystem
        org and course are optional strings that will be used in the generated modules
            url identifiers
        """
        raise NotImplementedError('Modules must implement from_xml to be parsable from xml')

    @classmethod
    def get_javascript(cls):
        """
        Return a dictionary containing some of the following keys:
            coffee: A list of coffeescript fragments that should be compiled and
                    placed on the page
            js: A list of javascript fragments that should be included on the page

        All of these will be loaded onto the page in the CMS
        """
        return cls.js

    def js_module_name(self):
        """
        Return the name of the javascript class to instantiate when
        this module descriptor is loaded for editing
        """
        return self.js_module


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
                self.metadata[attr] = metadata[attr]

    def get_children(self):
        """Returns a list of XModuleDescriptor instances for the children of this module"""
        if self._child_instances is None:
            self._child_instances = []
            for child_loc in self.definition.get('children', []):
                child = self.system.load_item(child_loc)
                child.inherit_metadata(self.metadata)
                self._child_instances.append(child)

        return self._child_instances

    def get_html(self):
        """
        Return the html used to edit this module
        """
        raise NotImplementedError("get_html() must be provided by specific modules")

    def xmodule_constructor(self, system):
        """
        Returns a constructor for an XModule. This constructor takes two arguments:
        instance_state and shared_state, and returns a fully nstantiated XModule
        """
        return partial(
            self.module_class,
            system,
            self.url,
            self.definition,
            metadata=self.metadata
        )


class DescriptorSystem(object):
    def __init__(self, load_item, resources_fs):
        """
        load_item: Takes a Location and returns an XModuleDescriptor
        resources_fs: A Filesystem object that contains all of the
            resources needed for the course
        """

        self.load_item = load_item
        self.resources_fs = resources_fs


class XMLParsingSystem(DescriptorSystem):
    def __init__(self, load_item, resources_fs, process_xml):
        """
        process_xml: Takes an xml string, and returns the the XModuleDescriptor created from that xml
        """
        DescriptorSystem.__init__(self, load_item, resources_fs)
        self.process_xml = process_xml
