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
    @classmethod
    def load_class(cls, identifier):
        classes = list(pkg_resources.iter_entry_points(cls.entry_point, name=identifier))
        if len(classes) > 1:
            log.warning("Found multiple classes for {entry_point} with identifier {id}: {classes}. Returning the first one.".format(
                entry_point=cls.entry_point,
                id=identifier,
                classes=", ".join([class_.module_name for class_ in classes])))

        if len(classes) == 0:
            raise ModuleMissingError(identifier)

        return classes[0].load()


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

    def handle_ajax(self, dispatch, get):
        ''' dispatch is last part of the URL. 
            get is a dictionary-like object ''' 
        return ""


class XModuleDescriptor(Plugin):

    entry_point = "xmodule.v1"

    @staticmethod
    def load_from_json(json_data, load_item):
        class_ = XModuleDescriptor.load_class(json_data['location']['category'])
        return class_.from_json(json_data, load_item)

    @classmethod
    def from_json(cls, json_data, load_item):
        """
        Creates an instance of this descriptor from the supplied json_data.

        json_data: Json data specifying the data, children, and metadata for the descriptor
        load_item: A function that takes an i4x url and returns a module descriptor
        """
        return cls(load_item=load_item, **json_data)

    def __init__(self,
                 load_item,
                 data=None,
                 children=None,
                 **kwargs):
        self.load_item = load_item
        self.data = data if data is not None else {}
        self.children = children if children is not None else []
        self.name = Location(kwargs.get('location')).name
        self._child_instances = None

    def get_children(self):
        """Returns a list of XModuleDescriptor instances for the children of this module"""
        if self._child_instances is None:
            self._child_instances = [self.load_item(child) for child in self.children]
        return self._child_instances


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
            return self.json # TODO: Return context as well -- files, etc. 
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
