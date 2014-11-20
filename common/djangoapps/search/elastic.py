from elasticsearch import Elasticsearch

from search.manager import SearchEngine


class ElasticSearchEngine(SearchEngine):

    _es = Elasticsearch()

    def __init__(self, index=None):
        super(ElasticSearchEngine, self).__init__(index)

    def index(self, doc_type, body, tags=None, **kwargs):
        if tags:
            body.update({"_tags": tags})

        self._es.index(
            index=self.index_name,
            doc_type=doc_type,
            body=body,
            **kwargs
        )

    def _translate_hits(self, es_response):
        response = {
            "took": es_response["took"],
            "total": es_response["hits"]["total"],
            "max_score": es_response["hits"]["max_score"],
        }

        def process_result(result):
            data = result.pop("_source")
            tags = data.pop("_tags") if "_tags" in data else {}

            result.update({
                "data": data,
                "tags": tags,
                "score": result["_score"]
            })

            return result

        results = [process_result(hit) for hit in es_response["hits"]["hits"]]
        response.update({"results": results})

        return response

    def search(self, query_string=None, field_dictionary=None, tag_dictionary=None, **kwargs):
        queries = []

        if query_string:
            queries.append({
                "query_string": {
                    "query": query_string
                }
            })

        if field_dictionary:
            for field in field_dictionary:
                queries.append({
                    "match": {
                        field: field_dictionary[field]
                    }
                })

        if tag_dictionary:
            for tag in tag_dictionary:
                queries.append({
                    "match": {
                        "_tags.{}".format(tag): tag_dictionary[tag]
                    }
                })

        query = {
            "match_all": {}
        }
        if len(queries) > 1:
            query = {
                "bool": {
                    "must": queries
                }
            }
        elif len(queries) > 0:
            query = queries[0]

        if kwargs is None:
            kwargs = {}
        if query:
            kwargs.update({
                "body": {"query": query}
            })

        es_response = self._es.search(
            index=self.index_name,
            **kwargs
        )

        return self._translate_hits(es_response)
