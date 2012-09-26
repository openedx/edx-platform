class StaticContent(object):
    def __init__(self, filename, name, content_type, data):
        self.filename = filename
        self.name = name
        self.content_type = content_type
        self.data = data

    @staticmethod
    def get_location_tag():
        return 'c4x'

    @staticmethod
    def compute_location_filename(org, course, name):
        return '/{0}/{1}/{2}/asset/{3}'.format(StaticContent.get_location_tag(), org, course, name)

