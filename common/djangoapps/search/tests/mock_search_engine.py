import copy
from search.manager import SearchEngine


class MockSearchEngine(SearchEngine):

    _mock_elastic = {}

    def __init__(self, index=None):
        super(MockSearchEngine, self).__init__(index)
        self._mock_elastic = {}

    def index(self, doc_type, body, tags=None, **kwargs):
        if self.index_name not in self._mock_elastic:
            self._mock_elastic[self.index_name] = {}

        _mock_index = self._mock_elastic[self.index_name]
        if doc_type not in _mock_index:
            _mock_index[doc_type] = []

        if tags:
            body.update({"_tags": tags})

        _mock_index[doc_type].append(body)

    def search(self, query_string=None, field_dictionary=None, tag_dictionary=None, **kwargs):
        # from nose.tools import set_trace; set_trace()
        if kwargs is None:
            kwargs = {}

        documents_to_search = []
        if "doc_type" in kwargs:
            if kwargs["doc_type"] in self._mock_elastic[self.index_name]:
                documents_to_search = self._mock_elastic[self.index_name][kwargs["doc_type"]]
        else:
            for index, doc_type in enumerate(self._mock_elastic[self.index_name]):
                documents_to_search.extend(self._mock_elastic[self.index_name][doc_type])

        if tag_dictionary:
            if field_dictionary is None:
                field_dictionary = {}
            for i, tag_name in enumerate(tag_dictionary):
                field_dictionary.update({
                    "_tags.{}".format(tag_name): tag_dictionary[tag_name]
                })

        if field_dictionary:
            def find_field(doc, field_name):
                field_chain = field_name.split('.', 1)
                if len(field_chain) > 1:
                    return find_field(doc[field_chain[0]], field_chain[1]) if field_chain[0] in doc else None
                else:
                    return doc[field_chain[0]] if field_chain[0] in doc else None

            for i, field_name in enumerate(field_dictionary):
                field_value = field_dictionary[field_name]
                documents_to_search = [d for d in documents_to_search if find_field(d, field_name) == field_value]

        if query_string:
            def has_string(dictionary_object, search_string):
                for i, name in enumerate(dictionary_object):
                    if isinstance(dictionary_object[name], dict):
                        return has_string(dictionary_object[name], search_string)
                    elif search_string in dictionary_object[name]:
                        return True
                return False

            search_strings = query_string.split(" ")
            documents_to_keep = []
            for search_string in search_strings:
                documents_to_keep.extend([d for d in documents_to_search if has_string(d, search_string)])

            documents_to_search = documents_to_keep

        # Finally, find duplicates and give them a higher score
        search_results = []
        max_score = 0
        while len(documents_to_search) > 0:
            current_doc = documents_to_search[0]
            score = len([d for d in documents_to_search if d == current_doc])
            if score > max_score:
                max_score = score
            documents_to_search = [d for d in documents_to_search if d != current_doc]

            data = copy.copy(current_doc)
            tags = data.pop("_tags") if "_tags" in current_doc else {}
            search_results.append(
                {
                    "score": score,
                    "tags": tags,
                    "data": data,
                }
            )

        return {
            "took": 10,
            "total": len(search_results),
            "max_score": max_score,
            "results": sorted(search_results, key=lambda k: k["score"])
        }
