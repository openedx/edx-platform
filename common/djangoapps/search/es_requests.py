import requests
import json
import os


class ElasticDatabase:

    def __init__(self, url, index_settings_file, *args):
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

        full_url = "/".join([self.url, index, type_, "_mapping"]) + "/"
        json_put_body = json.dumps({type_: json_mapping})
        return requests.put(full_url, data=json_put_body)

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

    def index_directory_transcripts(self, directory, index, type_):
        """Indexes all transcripts that are present in a given directory

        Will recursively go through the directory and assume all .srt.sjson files are transcript"""
        srt_check = lambda name: name[-10:] == ".srt.sjson"
        # Needs to be lazily evaluated
        transcripts = (name for name in os.walk(directory) if srt_check(name))

    def index_transcript(self, transcript_file, index, type_):
        file_uuid = transcript_file[transcript_file.find("/"):-10]
        with open(transcript_file, 'rb') as transcript:
            try:
                string = " ".join(json.loads(transcript)["text"])
            except:
                return "INVALID JSON"

    def setup_index(self, index):
        """Creates a new elasticsearch index, returns the response it gets"""
        full_url = "/".join([self.url, index]) + "/"
        return requests.post(full_url, data=json.dumps(self.index_settings))

    def add_index_settings(self, index, index_settings=None):
        index_settings = index_settings or self.index_settings
        full_url = "/".join([self.url, index]) + "/"
        #closing the index so it can be changed
        requests.post(full_url+"/_close")
        response = requests.post(full_url+"/_settings", data=json.dumps(index_settings))
        #reopening the index so it can be read
        requests.post(full_url+"/_open")
        return response

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
print test.setup_index("transcript")._content
print test.get_index_settings("transcript")
print test.setup_type("transcript", "cleaning", mapping)._content
test.get_type_mapping("transcript", "cleaning")
