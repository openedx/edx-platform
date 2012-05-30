import courseware.progress

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

        if system: 
            ## These are temporary; we really should go 
            ## through self.system. 
            self.ajax_url = system.ajax_url
            self.tracker = system.track_function
            self.filestore = system.filestore
            self.render_function = system.render_function
        self.system = system

    ### Functions used in the LMS

    def get_completion(self):
        ''' This is mostly unimplemented. 
            It gives a progress indication -- e.g. 30 minutes of 1.5 hours watched. 3 of 5 problems done, etc. '''
        return courseware.progress.completion()
    
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

    # TODO: 
    # def get_header_js(self):
    #     ''' Filename of common js that needs to be included in the header
    #     '''
    #     raise NotImplementedError

    def get_init_js(self):
        ''' JavaScript code to be run when problem is shown. Be aware
        that this may happen several times on the same page
        (e.g. student switching tabs). Common functions should be put
        in the main course .js files for now. ''' 
        return ""

    def get_destroy_js(self):
        ''' JavaScript called to destroy the problem (e.g. when a user switches to a different tab). 
            We make an attempt, but not a promise, to call this when the user closes the web page. 
        '''
        return ""

    def handle_ajax(self, dispatch, get):
        ''' dispatch is last part of the URL. 
            get is a dictionary-like object ''' 
        return ""

    ### Functions used in the CMS
    def get_xml(self):
        ''' For conversions between JSON and legacy XML representations.
        '''
        if self.xml: 
            return self.xml
        else: 
            raise NotImplementedError

    def get_json(self):
        ''' For conversions between JSON and legacy XML representations.
        '''
        if self.json: 
            raise NotImplementedError
            return self.json # TODO: Return context as well -- files, etc. 
        else: 
            raise NotImplementedError

    def handle_cms_json(self):
        raise NotImplementedError

    def render(self, size):
        ''' Size: [thumbnail, small, full] 
        Small ==> what we drag around
        Full ==> what we edit
        '''
        raise NotImplementedError
