from lxml import etree
import pkg_resources
import logging

from keystore import Location

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
        Initialized on access with __init__, first time with state=None, and
        then with state

        See the HTML module for a simple example
    '''
    id_attribute='id' # An attribute guaranteed to be unique

    @classmethod
    def get_xml_tags(c):
        ''' Tags in the courseware file guaranteed to correspond to the module '''
        return []
        
    @classmethod
    def get_usage_tags(c):
        ''' We should convert to a real module system
            For now, this tells us whether we use this as an xmodule, a CAPA response type
            or a CAPA input type '''
        return ['xmodule']

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
        children = [self.module_from_xml(e) for e in self.__xmltree]
        return children            

    def rendered_children(self):
        '''
        Render all children. 
        This really ought to return a list of xmodules, instead of dictionaries
        '''
        children = [self.render_function(e) for e in self.__xmltree]
        return children            

    def __init__(self, system = None, xml = None, item_id = None, 
                 json = None, track_url=None, state=None):
        ''' In most cases, you must pass state or xml'''
        if not item_id: 
            raise ValueError("Missing Index")
        if not xml and not json:
            raise ValueError("xml or json required")
        if not system:
            raise ValueError("System context required")

        self.xml = xml
        self.json = json
        self.item_id = item_id
        self.state = state
        self.DEBUG = False
        
        self.__xmltree = etree.fromstring(xml) # PRIVATE

        if system: 
            ## These are temporary; we really should go 
            ## through self.system. 
            self.ajax_url = system.ajax_url
            self.tracker = system.track_function
            self.filestore = system.filestore
            self.render_function = system.render_function
            self.module_from_xml = system.module_from_xml
            self.DEBUG = system.DEBUG
        self.system = system

    ### Functions used in the LMS

    def get_state(self):
        ''' State of the object, as stored in the database 
        '''
        return ""

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
    def load_from_xml(xml_data, system, org=None, course=None, default_class=None):
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
            goals: A list of strings of learning goals associated with this module
        """
        self.system = system
        self.definition = definition if definition is not None else {}
        self.name = Location(kwargs.get('location')).name
        self.type = Location(kwargs.get('location')).category
        self.url = Location(kwargs.get('location')).url()

        # For now, we represent goals as a list of strings, but this
        # is one of the things that we are going to be iterating on heavily
        # to find the best teaching method
        self.goals = kwargs.get('goals', [])

        self._child_instances = None

    def get_children(self):
        """Returns a list of XModuleDescriptor instances for the children of this module"""
        if self._child_instances is None:
            self._child_instances = [self.system.load_item(child) for child in self.definition.get('children', [])]

        return self._child_instances

    def get_html(self):
        """
        Return the html used to edit this module
        """
        raise NotImplementedError("get_html() must be provided by specific modules")

    def get_xml(self):
        ''' For conversions between JSON and legacy XML representations.
        '''
        if self.xml:
            return self.xml
        else:
            raise NotImplementedError("JSON->XML Translation not implemented")

    def get_json(self):
        ''' For conversions between JSON and legacy XML representations.
        '''
        if self.json:
            raise NotImplementedError
            return self.json  # TODO: Return context as well -- files, etc.
        else:
            raise NotImplementedError("XML->JSON Translation not implemented")

    #def handle_cms_json(self):
    #    raise NotImplementedError

    #def render(self, size):
    #    ''' Size: [thumbnail, small, full] 
    #    Small ==> what we drag around
    #    Full ==> what we edit
    #    '''
    #    raise NotImplementedError


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
