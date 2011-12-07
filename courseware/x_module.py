class XModule:
    ''' Implements a generic learning module. 
        Initialized on access with __init__, first time with state=None, and
        then with state
    '''
    def get_xml_tags():
        ''' Tags in the courseware file guaranteed to correspond to the module '''
        return []
        
    def get_id_attribute():
        ''' An attribute in the XML scheme that is guaranteed unique. '''
        return "name"

    def get_state(self):
        return ""

    def get_score(self):
        return None

    def max_score(self):
        return None

    def get_html(self):
        return "Unimplemented"

    def handle_ajax(self, json):
        return 

    def __init__(self, xml, item_id, ajax_url, track_url, state=None):
        self.xml=xml
        self.item_id=item_id
        self.ajax_url=ajax_url
        self.track_url=track_url
        self.state=state
