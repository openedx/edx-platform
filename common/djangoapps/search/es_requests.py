import requests
import json


class ElasticDatabase:

    def __init__(self, url, index_settings_file, analyzer_file, *args):
        """
        Will initialize elastic search object with any indices specified by args

        specifically the url should be something of the form `http://localhost:9200`
        importantly do not include a slash at the end of the url name.

        args should be a list of dictionaries, each dictionary specifying a JSON mapping
        to be used for a specific type.

        Example Dictionary:
            {"index": "transcript", "type": "6-002x", "mapping":
                {
                "properties" : {
                    "searchable_text": {
                        "type": "string",
                        "store": "yes",
                        "index": "analyzed"
                       }
                    }
                }
            }

        Eventually we will support different configuration files for different indices, but
        since this is only indexing transcripts right now it seems excessive"""

        self.url = url
        self.args = args
        self.index_settings = json.loads(open(index_settings_file, 'rb').read())
        self.index_settings['analysis'] = json.loads(open(analyzer_file).read())

    def parse_args(self):
        for mapping in self.args:
            try:
                json_mapping = json.loads(mapping)
            except ValueError:
                print "Badly formed JSON args, please check your mappings file"
                break

            try:
                index = json_mapping['index']
                type_ = json_mapping['type']
                mapping = json_mapping['mapping']
                self.setup_index(index)
                self.setup_type(index, type_, mapping)
            except KeyError:
                print "Could not find needed keys. Keys found: "
                print mapping.keys()
                continue

    def setup_type(self, index, type_, json_mapping):
        """
        json_mapping should be a dictionary starting at the properties level of a mapping.

        The type level will be added, so if you include it things will break. The purpose of this
        is to encourage loose coupling between types and mappings for better code
        """

        full_url = "/".join([self.url, index, type_, "_mapping"])
        json_put_body = {type_: json_mapping}
        requests.put(full_url, data=json_put_body)

    def has_index(self, index):
        """Checks to see if a given index exists in the database returns existance boolean,

        If this returns something other than a 200 or a 404 something is wrong and so we error"""
        full_url = "/".join([self.url, index])
        status = requests.head(full_url).status_code
        if status == 200:
            return True
        if status == 404:
            return False
        else:
            print "Got an unexpected reponse code: " + str(status)
            raise

    def setup_index(self, index):
        """Creates a new elasticsearch index, returns the response it gets"""
        full_url = "/".join([self.url, index]) + "/"
        return requests.put(full_url, data=self.index_settings)

    def index_data(self, index, type_, id_, data):
        """Data should be passed in as a dictionary, assumes it matches the given mapping"""
        full_url = "/".join([self.url, index, type_, id_])
        response = requests.put(full_url, json.dumps(data))
        return json.loads(response)['ok']

    def get_index_settings(self, index):
        """Returns the current settings of """
        full_url = "/".join([self.url, index, "_settings"])
        return json.loads(requests.get(full_url)._content)

    def get_type_mapping(self, index, type_):
        full_url = "/".join([self.url, index, type_, "_mapping"])
        return json.loads(requests.get(full_url)._content)

url = "https://localhost:9200"
settings_file = "settings.json"
mapping = json.loads(open("mapping.json", 'rb').read())
analyzer = "analyzer.json"

test = ElasticDatabase("http://localhost:9200", settings_file, analyzer)
test.setup_index("transcript")
print test.get_index_settings("transcript")
test.setup_type("transcript", "cleaning", mapping)
print test.get_type_mapping("transcript", "cleaning")

