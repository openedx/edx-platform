import requests
import json
import os
import re


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

    def os_walk_transcript(self, walk_results):
        """Takes the results of os.walk on the data directory and returns a list of absolute paths"""
        file_check = lambda walk: len(walk[2]) > 0
        srt_prelim = lambda walk: ".srt.sjson" in " ".join(walk[2])
        relevant_results = (entry for entry in walk_results if file_check(entry) and srt_prelim(entry))
        return (self.os_path_tuple_srts(result) for result in relevant_results)

    def os_path_tuple_srts(self, os_walk_tuple):
        """Given the path tuples from the os.walk method, constructs absolute paths to transcripts"""
        srt_check = lambda file_name: file_name[-10:] == ".srt.sjson"
        directory, subfolders, file_paths = os_walk_tuple
        return [os.path.join(directory, file_path) for file_path in file_paths if srt_check(file_path)]

    def index_directory_transcripts(self, directory, index, type_):
        """Indexes all transcripts that are present in a given directory

        Will recursively go through the directory and assume all .srt.sjson files are transcript"""
        # Needs to be lazily evaluatedy
        id_ = 1
        transcripts = self.os_walk_transcript(os.walk(directory))
        for transcript_list in transcripts:
            for transcript in transcript_list:
                print self.index_transcript(index, type_, str(id_), transcript)
                id_ += 1

    def index_transcript(self, index, type_, id_, transcript_file):
        """opens and indexes the given transcript file as the given index, type, and id"""
        file_uuid = transcript_file.rsplit("/")[-1][:-10]
        transcript = open(transcript_file, 'rb').read()
        #try:
        searchable_text = " ".join(filter(None, json.loads(transcript)["text"])).replace("\n", " ")
        data = {"searchable_text": searchable_text, "uuid": file_uuid}
        #except:
        #   return "INVALID JSON: " + file_uuid
        return self.index_data(index, type_, id_, data)._content

    def setup_index(self, index):
        """Creates a new elasticsearch index, returns the response it gets"""
        full_url = "/".join([self.url, index]) + "/"
        return requests.post(full_url, data=json.dumps(self.index_settings))

    def add_index_settings(self, index, index_settings=None):
        """Allows the editing of an index's settings"""
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
        return response

    def get_index_settings(self, index):
        """Returns the current settings of a given index"""
        full_url = "/".join([self.url, index, "_settings"])
        return json.loads(requests.get(full_url)._content)

    def get_type_mapping(self, index, type_):
        """Return the current mapping of the indicated type"""
        full_url = "/".join([self.url, index, type_, "_mapping"])
        return json.loads(requests.get(full_url)._content)

    def generate_dictionary(self, index, type_, output_file):
        """Generates a suitable pyenchant dictionary based on the current state of the database"""
        base_url = "/".join([self.url, index, type_])
        words = set()
        id_ = 1
        status_code = 200
        while status_code == 200:
            transcript = requests.get(base_url+"/"+str(id_))
            status_code = transcript.status_code
            try:
                text = json.loads(transcript._content)["_source"]["searchable_text"]
                words |= set(re.findall(r'[a-z]+', text.lower()))
            except KeyError:
                pass
            id_ += 1
            print id_
        with open(output_file, 'wb') as dictionary:
            for word in words:
                dictionary.write(word + "\n")

url = "https://localhost:9200"
settings_file = "settings.json"

test = ElasticDatabase("http://localhost:9200", settings_file)
#print test.setup_index("transcript-index")._content
#print test.get_index_settings("transcript-index")
#print test.setup_type("transcript", "cleaning", mapping)._content
#print test.get_type_mapping("transcript-index", "transcript")
#print test.index_directory_transcripts("/home/slater/edx_all/data", "transcript-index", "transcript")
test.generate_dictionary("transcript-index", "transcript", "pyenchant_corpus.txt")
