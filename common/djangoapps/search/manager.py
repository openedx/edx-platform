from django.conf import settings


class SearchEngine(object):

    index_name = "courseware"

    def __init__(self, index=None):
        if index:
            self.index_name = index

    def index(self, doc_type, body, tags=None, **kwargs):
        pass

    def search(self, query_string=None, field_dictionary=None, tag_dictionary=None, **kwargs):
        return None

    def search_string(self, query_string, **kwargs):
        return self.search(query_string=query_string, **kwargs)

    def search_fields(self, field_dictionary, **kwargs):
        return self.search(field_dictionary=field_dictionary)

    def search_tags(self, tag_dictionary, **kwargs):
        return self.search(tag_dictionary=tag_dictionary)

    @staticmethod
    def get_search_engine(index=None):
        return settings.SEARCH_ENGINE(index=index)
