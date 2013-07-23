import requests
import json
import os
import re
from pymongo import MongoClient
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFSyntaxError
from cStringIO import StringIO as cIO
from StringIO import StringIO as IO


class MongoIndexer:

    def __init__(self, host='localhost', port=27017, content_database='xcontent', file_collection="fs.files",
                 chunk_collection="fs.chunks", module_database='xmodule', module_collection='modulestore'):
        self.host = host
        self.port = port
        self.client = MongoClient(host, port)
        self.content_db = self.client[content_database]
        self.module_db = self.client[module_database]
        try:
            self.content_db.collection_names().index(file_collection)
        except ValueError:
            print "No collection named: " + file_collection
            raise
        try:
            self.content_db.collection_names().index(chunk_collection)
        except ValueError:
            print "No collection named: " + chunk_collection
        try:
            self.module_db.collection_names().index(module_collection)
        except ValueError:
            print "No collection named: " + module_collection
        self.file_collection = self.content_db[file_collection]
        self.chunk_collection = self.content_db[chunk_collection]
        self.module_collection = self.module_db[module_collection]

    def find_files_with_type(self, file_ending):
        """Returns a cursor for content files matching given type"""
        return self.file_collection.find({"filename": re.compile(".*?"+re.escape(file_ending))})

    def find_chunks_with_type(self, file_ending):
        """Returns a chunk cursor for content files matching given type"""
        return self.chunk_collection.find({"files_id.name": re.compile(".*?"+re.escape(file_ending))})

    def find_modules_by_category(self, category):
        """Returns a cursor for all xmodules matching given category"""
        return self.module_collection.find({"_id.category": category})

    def find_transcript_content(self, mongo_element):
        """Finds the corresponding chunk to the file element from a cursor similar to that from find_transcripts"""
        filename = mongo_element["_id"]["name"]
        database_object = self.chunk_collection.find_one({"files_id.name": filename})
        return json.loads(database_object["data"].decode())["text"]

    def pdf_to_text(self, mongo_element):
        onlyAscii = lambda s: "".join(c for c in s if ord(c) < 128)
        resource = PDFResourceManager()
        return_string = cIO()
        params = LAParams()
        converter = TextConverter(resource, return_string, codec='utf-8', laparams=params)
        fake_file = IO(mongo_element["data"].__str__())
        try:
            process_pdf(resource, converter, fake_file)
        except PDFSyntaxError:
            print mongo_element["files_id"]["name"] + " cannot be read, moving on."
            return ""
        text_value = onlyAscii(return_string.getvalue()).replace("\n", " ")
        return text_value

    def searchable_text_from_problem_data(self, mongo_element):
        """The data field from the problem is in weird xml, which is good for functionality, but bad for search"""
        data = mongo_element["definition"]["data"]
        paragraphs = " ".join([text for text in re.findall("<p>(.*?)</p>", data) if text is not "Explanation"])
        cleaned_text = re.sub("\\(.*?\\)", "", paragraphs).replace("\\", "")
        remove_tags = re.sub("<[a-zA-Z0-9/\.\= \"_-]+>", "", cleaned_text)
        remove_repetitions = re.sub(r"(.)\1{4,}", "", remove_tags)
        print remove_repetitions

    def module_for_uuid(self, transcript_uuid):
        """Given the transcript uuid found from the xcontent database, returns the mongo document for the video"""
        regex_pattern = re.compile(".*?"+str(transcript_uuid)+".*?")
        video_module = self.module_collection.find_one({"definition.data": regex_pattern})
        return video_module

    def uuid_from_file_name(self, file_name):
        """Returns a youtube uuid given the filename of a transcript"""
        print file_name
        if file_name[:5] == "subs_":
            file_name = file_name[5:]
        return file_name[:file_name.find(".")]

    def index_all_lecture_slides(self, es_instance, index):
        cursor = self.find_chunks_with_type(".pdf")
        for i in range(0, cursor.count()):
            item = cursor.next()
            # Not sure if this true is for every course, but it seems to
            # be a sensible limitations for the courses on my local machine
            if item["files_id"]["name"][:3] == "lec":
                course = item["files_id"]["course"]
                org = item["files_id"]["org"]
                # The lecture slides don't seem to have any kind of uuid or guid
                uuid = item["files_id"]["name"]
                display_name = org + " " + course + " " + item["files_id"]["name"]
                searchable_text = self.pdf_to_text(item)
                data = {"course": course, "org": org, "uuid": uuid, "searchable_text": searchable_text,
                        "display_name": display_name}
                type_ = course.replace(".", "-")
                print es_instance.index_data(index, type_, data)._content

    def index_all_problems(self, es_instance, index):
        cursor = self.find_modules_by_category("problem")
        for i in range(0, cursor.count()):
            item = cursor.next()
            course = item["_id"]["course"]
            org = item["_id"]["org"]
            uuid = item["_id"]["name"]
            display_name = org + " " + course + " " + item["metadata"]["display_name"]
            searchable_text = self.searchable_text_from_problem_data(item)
            data = {"course": course, "org": org, "uuid": uuid, "searchable_text": searchable_text,
                    "display_name": display_name}
            type_ = course.replace(".", "-")
            print es_instance.index_data(index, type_, data)._content

    def index_all_transcripts(self, es_instance, index):
        cursor = self.find_files_with_type(".srt.sjson")
        for i in range(0, cursor.count()):
            item = cursor.next()
            course = item["_id"]["course"]
            org = item["_id"]["org"]
            uuid = self.uuid_from_file_name(item["_id"]["name"])
            video_module = self.module_for_uuid(uuid)
            try:
                display_name = org + " " + course + " " + video_module["metadata"]["display_name"]
            except TypeError:
                print "Could not find module for: " + uuid
                display_name = org + " " + course
            transcript = " ".join(self.find_transcript_content(item))
            data = {"course": course, "org": org, "uuid": uuid, "searchable_text": transcript,
                    "display_name": display_name}
            type_ = course.replace(".", "-")
            print es_instance.index_data(index, type_, data)._content


class ElasticDatabase:

    def __init__(self, url, index_settings_file, *args):
        """
        Will initialize elastic search object with any indices specified by args
        specifically the url should be something of the form `http://localhost:9200`
        importantly do not include a slash at the end of the url name.

        args should be a list of dictionaries, each dictionary specifying a JSON mapping
        to be used for a specific type. See settings.json for a more in-depth example

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
        transcripts = self.os_walk_transcript(os.walk(directory))
        for transcript_list in transcripts:
            for transcript in transcript_list:
                print self.index_transcript(index, type_, transcript)

    def index_transcript(self, index, type_, transcript_file):
        """opens and indexes the given transcript file as the given index, type, and id"""
        file_uuid = transcript_file.rsplit("/")[-1][:-10]
        transcript = open(transcript_file, 'rb').read()
        searchable_text = " ".join(filter(None, json.loads(transcript)["text"])).replace("\n", " ")
        data = {"searchable_text": searchable_text, "uuid": file_uuid}
        return self.index_data(index, type_, data)._content

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
        response = requests.post(full_url+"/", data=json.dumps(index_settings))
        #reopening the index so it can be read
        requests.post(full_url+"/_open")
        return response

    def index_data(self, index, type_, data):
        """Data should be passed in as a dictionary, assumes it matches the given mapping"""
        full_url = "/".join([self.url, index, type_]) + "/"
        response = requests.post(full_url, json.dumps(data))
        return response

    def get_index_settings(self, index):
        """Returns the current settings of a given index"""
        full_url = "/".join([self.url, index, "_settings"])
        return json.loads(requests.get(full_url)._content)

    def delete_index(self, index):
        full_url = "/".join([self.url, index])
        return requests.delete(full_url)

    def delete_type(self, index, type_):
        full_url = "/".join([self.url, index, type_])
        return requests.delete(full_url)

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

url = "http://localhost:9200"
settings_file = "settings.json"

mongo = MongoIndexer()

test = ElasticDatabase(url, settings_file)
#print test.delete_index("transcript-index")
print test.add_index_settings("slides-index")._content
print test.get_index_settings("slides-index")
mongo.index_all_lecture_slides(test, "slides-index")

#print test.setup_type("transcript", "cleaning", mapping)._content
#print test.get_type_mapping("transcript-index", "2-1x")
#print test.index_directory_transcripts("/home/slater/edx_all/data", "transcript-index", "transcript")
# test.generate_dictionary("transcript-index", "transcript", "pyenchant_corpus.txt")
