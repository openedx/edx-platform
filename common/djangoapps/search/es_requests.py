import requests
import json
import os
import re
import urllib
import base64
from pymongo import MongoClient
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFSyntaxError
from cStringIO import StringIO as cIO
from StringIO import StringIO as IO
from wand.image import Image
from wand.exceptions import DelegateError, MissingDelegateError, CorruptImageError
from xhtml2pdf import pisa as pisa


class MongoIndexer:

    def __init__(
        self, host='localhost', port=27017, content_database='xcontent', file_collection="fs.files",
        chunk_collection="fs.chunks", module_database='xmodule', module_collection='modulestore'
    ):
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
            raise
        try:
            self.module_db.collection_names().index(module_collection)
        except ValueError:
            print "No collection named: " + module_collection
            raise
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

    def find_categories_with_regex(self, category, regex):
        return self.module_collection.find({"_id.category": category, "definition.data": regex})

    def find_asset_with_name(self, name):
        return self.chunk_collection.find_one({"files_id.category": "asset", "files_id.name": name})

    def find_transcript_content(self, mongo_element):
        """Finds the corresponding chunk to the file element from a cursor similar to that from find_transcripts"""
        filename = mongo_element["_id"]["name"]
        database_object = self.chunk_collection.find_one({"files_id.name": filename})
        try:
            return filter(None, json.loads(database_object["data"].decode('utf-8', "ignore"))["text"])
        except ValueError:
            return ["n/a"]

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
        try:
            paragraphs = " ".join([text for text in re.findall("<p>(.*?)</p>", data) if text is not "Explanation"])
        except TypeError:
            paragraphs = "n/a"
        cleaned_text = re.sub("\\(.*?\\)", "", paragraphs).replace("\\", "")
        remove_tags = re.sub("<[a-zA-Z0-9/\.\= \"_-]+>", "", cleaned_text)
        remove_repetitions = re.sub(r"(.)\1{4,}", "", remove_tags)
        return remove_repetitions

    def module_for_uuid(self, transcript_uuid):
        """Given the transcript uuid found from the xcontent database, returns the mongo document for the video"""
        regex_pattern = re.compile(".*?"+str(transcript_uuid)+".*?")
        video_module = self.module_collection.find_one({"definition.data": regex_pattern})
        return video_module

    def uuid_from_file_name(self, file_name):
        """Returns a youtube uuid given the filename of a transcript"""
        if "subs_" in file_name:
            file_name = file_name[5+file_name.find("subs_"):]
        elif file_name[:2] == "._":
            file_name = file_name[2:]
        return file_name[:file_name.find(".")]

    def thumbnail_from_uuid(self, uuid):
        image = urllib.urlopen("http://img.youtube.com/vi/" + uuid + "/0.jpg")
        return base64.b64encode(image.read())

    def thumbnail_from_pdf(self, pdf):
        try:
            with Image(blob=pdf) as img:
                return base64.b64encode(img.make_blob('jpg'))
        except (DelegateError, MissingDelegateError, CorruptImageError):
            raise

    def thumbnail_from_html(self, html):
        pseudo_dest = cIO()
        pisa.CreatePDF(IO(html), pseudo_dest)
        return self.thumbnail_from_pdf(pseudo_dest.getvalue())

    def vertical_url_from_mongo_element(self, mongo_element):
        """Given a mongo element, returns the url after courseware"""
        name = lambda x: x["_id"]["name"]
        element_name = name(mongo_element)
        vertical = self.module_collection.find_one({"definition.children": re.compile(".*?"+element_name+".*?")})
        if vertical:
            index = next(i for i, entry in enumerate(vertical["definition"]["children"]) if element_name in entry)
            sequential = self.module_collection.find_one({
                "definition.children": re.compile(".*?"+name(vertical)+".*?"),
                "_id.course": vertical["_id"]["course"]
            })
            if sequential and sequential["_id"]:
                chapter = self.module_collection.find_one({
                    "definition.children": re.compile(".*?"+name(sequential)+".*?"),
                    "_id.course": sequential["_id"]["course"]
                })
                if chapter and chapter["_id"]:
                    return "/".join([name(chapter), name(sequential), str(index+1)])
                else:
                    print "No Chapter for: " + sequential["metadata"]["display_name"]
                    return None
            else:
                print "No Sequential for: " + vertical["metadata"]["display_name"]
                return None
        else:
            return None

    def course_name_from_mongo_element(self, mongo_element):
        course_element = self.module_collection.find_one({
            "_id.course": mongo_element["_id"]["course"],
            "_id.category": "course"
        })
        return course_element["_id"]["name"]

    def index_all_pdfs(self, es_instance, index):
        cursor = self.find_categories_with_regex("html", re.compile(".*?/asset/.*?\.pdf.*?"))
        for i in range(0, cursor.count()):
            item = cursor.next()
            course = item["_id"]["course"]
            org = item["_id"]["org"]
            uuid = item["_id"]["name"]
            course_section = self.course_name_from_mongo_element(item)
            display_name = item.get("metadata", {"display_name": ""}).get("display_name", "") + " (" + course + ")"
            url = self.vertical_url_from_mongo_element(item)
            if not url:
                continue
            name = re.sub(r'(.*?)(/asset/)(.*?)(\.pdf)(.*?)$', r'\3'+".pdf", item["definition"]["data"])
            asset = self.find_asset_with_name(name)
            if not asset:
                continue
            searchable_text = self.pdf_to_text(asset)
            try:
                thumbnail = self.thumbnail_from_pdf(asset["data"].__str__())
            except (DelegateError, MissingDelegateError, CorruptImageError):
                print "Slide: " + uuid + " is corrupt."
                continue
            data = {
                "course": course, "org": org, "course_section": "/".join([org, course, course_section]), "uuid": uuid,
                "searchable_text": searchable_text, "display_name": display_name, "url": url, "thumbnail": thumbnail
            }
            print es_instance.index_data(index, course, data)._content

    def index_all_problems(self, es_instance, index):
        cursor = self.find_modules_by_category("problem")
        for i in range(0, cursor.count()):
            item = cursor.next()
            course = item["_id"]["course"]
            org = item["_id"]["org"]
            uuid = item["_id"]["name"]
            url = self.vertical_url_from_mongo_element(item)
            course_section = self.course_name_from_mongo_element(item)
            if not url:
                continue
            display_name = item.get("metadata", {"display_name": ""}).get("display_name", "") + " (" + course + ")"
            searchable_text = self.searchable_text_from_problem_data(item)
            thumbnail = self.thumbnail_from_html(item["definition"]["data"])
            data = {
                "course": course, "course_section": "/".join([org, course, course_section]), "org": org, "uuid": uuid,
                "searchable_text": searchable_text, "display_name": display_name, "url": url, "thumbnail": thumbnail
            }
            print es_instance.index_data(index, course, data)._content

    def index_all_transcripts(self, es_instance, index):
        cursor = self.find_files_with_type(".srt.sjson")
        for i in range(0, cursor.count()):
            item = cursor.next()
            course = item["_id"]["course"]
            org = item["_id"]["org"]
            uuid = self.uuid_from_file_name(item["_id"]["name"])
            video_module = self.module_for_uuid(uuid)
            course_section = self.course_name_from_mongo_element(item)
            if not video_module:
                print "No module for: " + str(uuid)
                continue
            url = self.vertical_url_from_mongo_element(video_module)
            if not url:
                continue
            display_name = item.get("metadata", {"display_name": ""}).get("display_name", "") + " (" + course + ")"
            transcript = " ".join(self.find_transcript_content(item))
            thumbnail = self.thumbnail_from_uuid(uuid)
            data = {
                "course": course, "course_section": "/".join([org, course, course_section]), "org": org, "uuid": uuid,
                "searchable_text": transcript, "display_name": display_name, 'url': url, 'thumbnail': thumbnail
            }
            print es_instance.index_data(index, course, data)._content


class ElasticDatabase:

    def __init__(self, url, index_settings_file):
        """
        Will initialize elastic search object with specified indices
        specifically the url should be something of the form `http://localhost:9200`
        importantly do not include a slash at the end of the url name."""

        self.url = url
        self.index_settings = json.loads(open(index_settings_file, 'rb').read())

    def setup_type(self, index, type_, json_mapping):
        """
        yaml_mapping should be a dictionary starting at the properties level of a mapping.

        The type level will be added, so if you include it things will break. The purpose of this
        is to encourage loose coupling between types and mappings for better code
        """

        full_url = "/".join([self.url, index, type_]) + "/"
        dictionary = json.loads(open(json_mapping).read())
        print dictionary
        return requests.post(full_url, data=json.dumps(dictionary))

    def has_index(self, index):
        """Checks to see if a given index exists in the database returns existance boolean,

        If this returns something other than a 200 or a 404 something is wrong and so we error"""
        full_url = "/".join([self.url, index])
        status = requests.head(full_url).status_code
        if status == 200:
            return True
        elif status == 404:
            return False
        else:
            print "Got an unexpected reponse code: " + str(status)
            raise

    def has_type(self, index, type_):
        """Same as has_index, but for a given type"""
        full_url = "/".join([self.url, index, type_])
        status = requests.head(full_url).status_code
        if status == 200:
            return True
        elif status == 404:
            return False
        else:
            print "Got an unexpected response code: " + str(status)
            raise

    def index_directory_files(self, directory, index, type_, silent=False, **kwargs):
        """Starts a pygrep instance and indexes all files in the given directory

        Available kwargs are file_ending, callback, and conserve_kwargs.
        Respectively these allow you to choose the file ending to be indexed, the
        callback used to do the indexing, and whether or not you would like to pass
        additional kwargs to the callback function."""
        # Needs to be lazily evaluatedy
        file_ending = kwargs.get("file_ending", ".srt.sjson")
        callback = kwargs.get("callback", self.index_transcript)
        conserve_kwargs = kwargs.get("conserve_kwargs", False)
        directoryCrawler = PyGrep(directory)
        all_files = directoryCrawler.grab_all_files_with_ending(file_ending)
        responses = []
        for file_list in all_files:
            for file_ in file_list:
                if conserve_kwargs:
                    responses.append(callback(index, type_, file_, silent, kwargs))
                else:
                    responses.append(callback(index, type_, file_, silent))
        return responses

    def index_transcript(self, index, type_, transcript_file, silent=False, id_=None):
        """opens and indexes the given transcript file as the given index, type, and id"""
        file_uuid = transcript_file.rsplit("/")[-1][:-10]
        transcript = open(transcript_file, 'rb').read()
        try:
            searchable_text = " ".join(filter(None, json.loads(transcript)["text"])).replace("\n", " ")
        except ValueError:
            if silent:
                searchable_text = "INVALID JSON"
            else:
                raise
        data = {"searchable_text": searchable_text, "uuid": file_uuid}
        if not id_:
            return self.index_data(index, type_, data)._content
        else:
            return self.index_data(index, type_, data, id_=id_)

    def setup_index(self, index):
        """Creates a new elasticsearch index, returns the response it gets"""
        full_url = "/".join([self.url, index]) + "/"
        return requests.put(full_url, data=json.dumps(self.index_settings))

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

    def index_data(self, index, type_, data, id_=None):
        """Data should be passed in as a dictionary, assumes it matches the given mapping"""
        if not id_:
            full_url = "/".join([self.url, index, type_]) + "/"
        else:
            full_url = "/".join([self.url, index, type_, id_])
        response = requests.post(full_url, json.dumps(data))
        return response

    def get_data(self, index, type_, id_):
        full_url = "/".join([self.url, index, type_, id_])
        return requests.get(full_url)

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


class PyGrep:

    def __init__(self, directory):
        self.directory = directory

    def grab_all_files_with_ending(self, file_ending):
        """Will return absolute paths to all files with given file ending in self.directory"""
        walk_results = os.walk(self.directory)
        file_check = lambda walk: len(walk[2]) > 0
        ending_prelim = lambda walk: file_ending in " ".join(walk[2])
        relevant_results = (entry for entry in walk_results if file_check(entry) and ending_prelim(entry))
        return (self.grab_files_from_os_walk(result, file_ending) for result in relevant_results)

    def grab_files_from_os_walk(self, os_walk_tuple, file_ending):
        """Made to interface with """
        format_check = lambda file_name: file_ending in file_name
        directory, subfolders, file_paths = os_walk_tuple
        return [os.path.join(directory, file_path) for file_path in file_paths if format_check(file_path)]


class EnchantDictionary:

    def __init__(self, esDatabase):
        self.es_instance = esDatabase

    def produce_dictionary(self, output_file, **kwargs):
        """Produces a dictionary or updates it depending on kwargs

        If no kwargs are given then this method will write a full dictionary including all
        entries in all indices and types and output it in an enchant-friendly way to the output file.

        Accepted kwargs are index, and source_file. If you want to index multiple types
        or indices you should pass them in as comma delimited strings. Source file should be
        an absolute path to an existing enchant-friendly dictionary file.

        max_results will also set the maximum number of entries to be used in generating the dictionary.
        Set to 50k by default"""
        index = kwargs.get("index", "_all")
        max_results = kwargs.get("max_results", 50000)
        words = set()
        if kwargs.get("source_file", None):
            words = set(open(kwargs["source_file"]).readlines())
        url = "/".join([self.es_instance.url, index, "_search?size="+str(max_results)+"&q=*.*"])
        response = requests.get(url)
        for entry in json.loads(response._content)['hits']['hits']:
            if entry["_source"]["searchable_text"]:
                text = entry["_source"]["searchable_text"]
                words |= set(re.findall(r'[a-z]+', text.lower()))
            else:
                continue
        with open(output_file, 'wb') as dictionary:
            for word in words:
                dictionary.write(word+"\n")


url = "http://localhost:9200"
settings_file = "settings.json"

mongo = MongoIndexer()


test = ElasticDatabase(url, settings_file)
dictionary = EnchantDictionary(test)
print test.delete_index("pdf-index")
print test.delete_index("transcript-index")
print test.delete_index("problem-index")
mongo.index_all_pdfs(test, "pdf-index")
mongo.index_all_transcripts(test, "transcript-index")
mongo.index_all_problems(test, "problem-index")
dictionary.produce_dictionary("pyenchant_corpus.txt", max_results=500000)

#print test.setup_type("transcript", "cleaning", mapping)._content
#print test.get_type_mapping("transcript-index", "2-1x")
#print test.index_directory_transcripts("/home/slater/edx_all/data", "transcript-index", "transcript")
#test.generate_dictionary("transcript-index", "transcript", "pyenchant_corpus.txt")
