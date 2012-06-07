from lxml import etree

def dummy_track(event_type, event):
    pass

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

    def get_name():
        name = self.__xmltree.get(name)
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


class XModuleDescriptor(object):
    def __init__(self, xml = None, json = None):
        if not xml and not json:
            raise "XModuleDescriptor must be initalized with XML or JSON"
        if not xml:
            raise NotImplementedError("Code does not have support for JSON yet")
        
        self.xml = xml
        self.json = json

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
