XASSET_LOCATION_TAG = 'c4x'
XASSET_SRCREF_PREFIX = 'xasset:'

class StaticContent(object):
    def __init__(self, filename, name, content_type, data, last_modified_at=None):
        self.filename = filename
        self.name = name
        self.content_type = content_type
        self.data = data
        self.last_modified_at = last_modified_at

    @staticmethod
    def compute_location_filename(org, course, name):
        return '/{0}/{1}/{2}/asset/{3}'.format(XASSET_LOCATION_TAG, org, course, name)

'''
Abstraction for all ContentStore providers (e.g. MongoDB)
'''
class ContentStore(object):
    def save(self, content):
        raise NotImplementedError

    def find(self, filename):
        raise NotImplementedError

            
