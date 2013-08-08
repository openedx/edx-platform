"""
General methods and classes for interaction with the Mongo Database and Elasticsearch instance
"""

import requests
import json
import os
import re
import urllib
import base64
import hashlib
import cStringIO
import StringIO
import logging

from django.conf import settings
from pymongo import MongoClient
from pdfminer.pdfinterp import PDFResourceManager, process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfparser import PDFSyntaxError
from wand.image import Image
from wand.exceptions import DelegateError, MissingDelegateError, CorruptImageError  # pylint: disable=E0611
from xhtml2pdf import pisa as pisa

log = logging.getLogger("mitx.courseware")
MONGO_COURSE_CACHE = {}


class ElasticDatabase:
    """
    This is a wrapper for Elastic Search that sits on top of the existent REST api.

    In a broad sense there are two layers in Elastic Search. The top level is
    an index. In this implementation indicies represent types of content (transcripts, problems, etc...).
    The second level, strictly below indicies, is a type.

    In this implementation types are hashed course ids (SHA1).

    In addition to those two levels of nesting, each individual piece of data has an id associated with it.
    Currently the id of each object is a SHA1 hash of its entire id field.

    Each index has "settings" associated with it. These are quite minimal, just specifying the number of
    nodes and shards the index is distributed across.

    Each type has a mapping associated with it. A mapping is essentially a database schema with some additional
    information surrounding search functionality, such as tokenizers and analyzers.

    Right now these settings are entirely specified through JSON in the settings.json file located within this
    directory. Most of the methods in this class serve to instantiate types and indices within the Elastic Search
    instance. Additionly there are methods for running basic queries and content indexing.
    """

    def __init__(self, settings_file=None):
        """
        Instantiates the ElasticDatabase file.

        This includes a url, which should point to the location of the elasticsearch server.
        The only other input here is the Elastic Search settings file, which is a JSON file
        that should be specified in the application settings file.
        """

        self.url = settings.ES_DATABASE
        if settings_file is None:
            current_directory = os.path.dirname(os.path.realpath(__file__))
            with open(os.path.join(current_directory, "settings.json")) as source:
                self.index_settings = json.load(source)
        else:
            with open(settings_file) as source:
                self.index_settings = json.load(source)

    def setup_type(self, index, type_, json_mapping):
        """
        Instantiates a type within the Elastic Search instance

        json_mapping should be a dictionary starting at the properties level of a mapping.

        The type level will be added, so if you include it things will break. The purpose of this
        is to encourage loose coupling between types and mappings for better code
        """

        full_url = "/".join([self.url, index, type_]) + "/"
        with open(json_mapping) as source:
            dictionary = json.load(source)
        dictionary = json.load(open(json_mapping))
        return requests.post(full_url, data=json.dumps(dictionary))

    def has_index(self, index):
        """
        Checks to see if the Elastic Search instance contains the given index,
        """

        full_url = "/".join([self.url, index])
        status = requests.head(full_url).status_code
        if status == 200:
            return True
        elif status == 404:
            return False

    def has_type(self, index, type_):
        """
        Same as has_index method, but for a given type
        """

        full_url = "/".join([self.url, index, type_])
        status = requests.head(full_url).status_code
        if status == 200:
            return True
        elif status == 404:
            return False

    def index_directory_files(
        self, directory, index, type_, silent=False, file_ending=".srt.sjson",
        callback=None, conserve_kwargs=False, **kwargs
    ):
        """
        Starts a pygrep instance and indexes all files in the given directory.

        Available kwargs are file_ending, callback, and conserve_kwargs.
        Respectively these allow you to choose the file ending to be indexed, the
        callback used to do the indexing, and whether or not you would like to pass
        your kwargs to the callback function
        """

        # Needs to be lazily evaluatedy
        if callback is None:
            callback = self.index_transcript
        directory_crawler = PyGrep(directory)
        all_files = directory_crawler.grab_all_files_with_ending(file_ending)
        responses = []
        for file_list in all_files:
            for file_ in file_list:
                if conserve_kwargs:
                    responses.append(callback(index, type_, file_, silent, **kwargs))
                else:
                    responses.append(callback(index, type_, file_, silent))
        return responses

    def searchable_text_from_transcript_file(self, transcript_file, silent=False):
        """
        Returns human-readable text string from raw transcript file
        """

        transcript = open(transcript_file, 'rb')
        try:
            searchable_text = " ".join(filter(None, json.load(transcript)["text"])).replace("\n", " ")
        except ValueError:
            if silent:
                searchable_text = transcript.read()
            else:
                raise
        return searchable_text

    def index_transcript(self, index, type_, transcript_file, silent=False, id_=None):
        """
        Indexes the given transcript file at the given index, type, and id
        """

        file_uuid = transcript_file.rsplit("/")[-1][:-len(".srt.sjson")]
        searchable_text = self.searchable_text_from_transcript_file(transcript_file, silent)
        sha_hash = hashlib.sha1(file_uuid).hexdigest()
        data = {"searchable_text": searchable_text, "uuid": file_uuid, "hash": sha_hash}
        print type(data)
        print data
        if not id_:
            return self.index_data(index, data, type_).content
        else:
            return self.index_data(index, data, type_, id_=id_)

    def setup_index(self, index):
        """
        Creates a new elasticsearch index, returns the response it gets
        """

        full_url = "/".join([self.url, index]) + "/"
        return requests.put(full_url, data=json.dumps(self.index_settings))

    def index_data(self, index, data, type_=None, id_=None):
        """
        Actually indexes given data at the indicated type and id.

        If no type or id is provided, this will assume that the type and id are
        contained within the data object passed to the index_data function in the
        hash and type_hash fields.

        Data should be a dictionary that matches the mapping of the given type.
        """

        if id_ is None:
            id_ = data["hash"]
        if type_ is None:
            type_ = data["type_hash"]
        full_url = "/".join([self.url, index, type_, id_])
        response = requests.post(full_url, json.dumps(data))
        return response

    def bulk_index(self, all_data):
        """
        Allows for bulk indexing of properly formatted json strings.
        Example:
        {"index": {"_index": "transcript-index", "_type": "course_hash", "_id": "id_hash"}}
        {"field1": "value1"...}

        Important: Bulk indexing is newline delimited, make sure the newlines are properly used
        """

        url = self.url + "/_bulk"
        return requests.post(url, data=all_data)

    def get_data(self, index, type_, id_):
        """
        Returns the data located at a specific index, type and id within the elasticsearch instance
        """

        full_url = "/".join([self.url, index, type_, id_])
        return requests.get(full_url)

    def get_index_settings(self, index):
        """
        Returns the current settings of a given index
        """

        full_url = "/".join([self.url, index, "_settings"])
        return json.loads(requests.get(full_url).content)

    def delete_index(self, index):
        """
        Deletes the index specified, along with all contained types and data
        """

        full_url = "/".join([self.url, index])
        return requests.delete(full_url)

    def delete_type(self, index, type_):
        """
        Same as delete_index, but for types
        """

        full_url = "/".join([self.url, index, type_])
        return requests.delete(full_url)

    def get_type_mapping(self, index, type_):
        """
        Return the mapping of the indicated type
        """

        full_url = "/".join([self.url, index, type_, "_mapping"])
        return json.loads(requests.get(full_url).content)


class MongoIndexer:
    """
    This class is the connection point between Mongo and ElasticSearch.
    """

    def __init__(
        self, host='localhost', port=27017, content_database='xcontent', file_collection="fs.files",
        chunk_collection="fs.chunks", module_database='xmodule', module_collection='modulestore',
        es_instance=ElasticDatabase()
    ):
        self.host = host
        self.port = port
        self.client = MongoClient(host, port)
        self.content_db = self.client[content_database]
        self.module_db = self.client[module_database]
        self.file_collection = self.content_db[file_collection]
        self.chunk_collection = self.content_db[chunk_collection]
        self.module_collection = self.module_db[module_collection]
        self.es_instance = es_instance

    def find_files_with_type(self, file_ending):
        """
        Returns a cursor for content files matching given type
        """

        return self.file_collection.find({"filename": re.compile(".*?" + re.escape(file_ending))}, timeout=False)

    def find_chunks_with_type(self, file_ending):
        """
        Returns a chunk cursor for content files matching given type
        """

        return self.chunk_collection.find({"files_id.name": re.compile(".*?" + re.escape(file_ending))}, timeout=False)

    def find_modules_by_category(self, category):
        """
        Returns a cursor for all xmodules matching given category
        """

        return self.module_collection.find({"_id.category": category}, timeout=False)

    def find_categories_with_regex(self, category, regex):
        """
        Returns a cursor matching all items in mongo where the category matches the given regex
        """

        return self.module_collection.find({"_id.category": category, "definition.data": regex}, timeout=False)

    def find_asset_with_name(self, name):
        """
        Returns a single asset whose filename exactly matches the one provided
        """

        return self.chunk_collection.find_one({"files_id.category": "asset", "files_id.name": name}, timeout=False)

    def find_modules_for_course(self, course):
        """
        Returns a cursor matching all modules in the given course
        """

        return self.module_collection.find({"_id.course": course}, timeout=False)

    def find_transcript_for_video_module(self, video_module):
        """
        Returns a transcript for a video given the module that contains it.

        The video module should be passed in as an element from some mongo cursor.
        """

        data = video_module.get("definition", {"data": ""}).get("data", "")
        if isinstance(data, dict):  # For some reason there are nested versions
            data = data.get("data", "")
        if isinstance(data, unicode) is False:  # for example videos
            return [""]
        uuid = self.uuid_from_video_module(video_module)
        name_pattern = re.compile(".*?" + uuid + ".*?")
        chunk = self.chunk_collection.find_one({"files_id.name": name_pattern})
        if chunk is None:
            return [""]
        elif "com.apple.quar" in chunk["data"].decode('utf-8', "ignore"):
            # This seemingly arbitrary error check brought to you by apple.
            # This is an obscure, barely documented occurance where apple broke tarballs
            # and decided to shove error messages into tar metadata which causes this.
            # https://discussions.apple.com/thread/3145071?start=0&tstart=0
            return [""]
        else:
            try:
                return " ".join(filter(None, json.loads(chunk["data"].decode('utf-8', "ignore"))["text"]))
            except ValueError:
                log.error("Transcript for: " + uuid + " is invalid")
                return chunk["data"].decode('utf-8', 'ignore')

    def pdf_to_text(self, mongo_element):
        """
        Returns human-readable text from a given pdf.

        The mongo element should be a member of fs.chunks, since this is expecting a binary
        representation of the pdf.

        It's worth noting that this method is relatively verbose, largely because mongo contains
        a number of invalid or semi-valid pdfs.
        """

        only_ascii = lambda s: "".join(c for c in s if ord(c) < 128)
        resource = PDFResourceManager()
        return_string = cStringIO.StringIO()
        params = LAParams()
        converter = TextConverter(resource, return_string, codec='utf-8', laparams=params)
        fake_file = StringIO.StringIO(mongo_element["data"].__str__())
        try:
            process_pdf(resource, converter, fake_file)
        except PDFSyntaxError:
            log.debug(mongo_element["files_id"]["name"] + " cannot be read, moving on.")
            return ""
        text_value = only_ascii(return_string.getvalue()).replace("\n", " ")
        return text_value

    def searchable_text_from_problem_data(self, mongo_element):
        """
        The data field from the problem is in weird xml, which is good for functionality, but bad for search
        """

        data = mongo_element["definition"]["data"]
        paragraphs = " ".join([text for text in re.findall(r"<p>(.*?)</p>", data) if text is not "Explanation"])
        paragraphs += " "
        paragraphs += " ".join([text for text in re.findall(r"<text>(.*?)</text>", data)])
        cleaned_text = re.sub(r"\\(.*?\\)", "", paragraphs).replace("\\", "")
        remove_tags = re.sub(r"<[a-zA-Z0-9/\.\= \"\'_-]+>", "", cleaned_text)
        remove_repetitions = re.sub(r"(.)\1{4,}", "", remove_tags)
        return remove_repetitions

    def uuid_from_file_name(self, file_name):
        """
        Returns a youtube uuid given the filename of a transcript
        """
        if "subs_" in file_name:
            file_name = file_name[5 + file_name.find("subs_"):]
        elif file_name[:2] == "._":
            file_name = file_name[2:]
        return file_name[:file_name.find(".")]

    def thumbnail_from_video_module(self, video_module):
        """
        Return an appropriate binary thumbnail for a given video module
        """

        data = video_module.get("definition", {"data": ""}).get("data", "")
        if "player.youku.com" in data:
        # Some videos use the youku player, this is just the default youku icon
        # Youku requires an api key to pull down relevant thumbnails, but
        # if that is ever present this should be switched. Right now it only applies to two videos.
            url = "https://lh6.ggpht.com/8_h5j6hiFXdSl5atSJDf8bJBy85b3IlzNWeRzOqRurfNVI_oiEG-dB3C0vHRclOG8A=w170"
            image = urllib.urlopen(url)
            return base64.b64encode(image.read())
        uuid = self.uuid_from_video_module(video_module)
        if uuid is False:
            url = "http://img.youtube.com/vi/Tt9g2se1LcM/4.jpg"
            image = urllib.urlopen(url)
            return base64.b64encode(image.read())
        image = urllib.urlopen("http://img.youtube.com/vi/" + uuid + "/0.jpg")
        return base64.b64encode(image.read())

    def uuid_from_video_module(self, video_module):
        """
        Returns the youtube uuid given a video module.

        Implementation right now is a little hacky since we don't actually have a specific
        value for the relevant uuid, though we implicitly refer to all videos by their 1.0
        speed youtube uuids throughout the database.

        Example of the data associated with a video_module:

        <video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">
        """

        data = video_module.get("definition", {"data": ""}).get("data", "")
        if isinstance(data, dict):
            data = data.get("data", "")
        uuids = data.split(",")
        if len(uuids) == 1:  # Some videos are just left over demos without links
            return False
        # The colon is kind of a hack to make sure there will always be a second element since
        # some entries don't have anything for the second entry
        speed_map = {(entry + ":").split(":")[0]: (entry + ":").split(":")[1] for entry in uuids}
        uuid = [value for key, value in speed_map.items() if "1.0" in key][0]
        return uuid

    def thumbnail_from_pdf(self, pdf):
        """
        Converts a pdf to a jpg. Currently just takes the first page.
        """

        try:
            with Image(blob=pdf) as img:
                return base64.b64encode(img.make_blob('jpg'))
        except (DelegateError, MissingDelegateError, CorruptImageError):
            raise

    def thumbnail_from_html(self, html):
        """
        Returns a binary thumbnail for a given html string.

        Right now the most straightforward way I could find of doing this was by converting
        this html to a pdf and then returning a jpg of that pdf.
        """
        pseudo_dest = cStringIO.StringIO()
        pisa.CreatePDF(StringIO.StringIO(html), pseudo_dest)
        return self.thumbnail_from_pdf(pseudo_dest.getvalue())

    def course_name_from_mongo_module(self, mongo_module):
        """
        Given a mongo_module, returns the name for the course element it belongs to
        """
        course_element = self.module_collection.find_one({
            "_id.course": mongo_module["_id"]["course"],
            "_id.category": "course"
        })
        return course_element["_id"]["name"]

    def basic_dict(self, mongo_module, type_):
        """
        Returns the part of the es schema that is the same for every object.
        """

        id_ = json.dumps(mongo_module["_id"])
        org = mongo_module["_id"]["org"]
        course = mongo_module["_id"]["course"]

        if not MONGO_COURSE_CACHE.get(course, False):
            MONGO_COURSE_CACHE[course] = self.course_name_from_mongo_module(mongo_module)
        offering = MONGO_COURSE_CACHE[course]

        course_id = "/".join([org, course, offering])
        hash_ = hashlib.sha1(id_).hexdigest()
        display_name = (
            mongo_module.get("metadata", {"display_name": ""}).get("display_name", "") +
            " (" + mongo_module["_id"]["course"] + ")"
        )
        searchable_text = self.get_searchable_text(mongo_module, type_)
        thumbnail = self.get_thumbnail(mongo_module, type_)
        type_hash = hashlib.sha1(course_id).hexdigest()
        return {
            "id": id_,
            "hash": hash_,
            "display_name": display_name,
            "course_id": course_id,
            "searchable_text": searchable_text,
            "thumbnail": thumbnail,
            "type_hash": type_hash
        }

    def get_searchable_text(self, mongo_module, type_):
        """
        Returns searchable text for a module. Defined for a module only
        """

        if type_.lower() == "pdf":
            name = re.sub(r'(.*?)(/asset/)(.*?)(\.pdf)(.*?)$', r'\3' + ".pdf", mongo_module["definition"]["data"])
            asset = self.find_asset_with_name(name)
            if not asset:
                searchable_text = ""
            else:
                searchable_text = self.pdf_to_text(asset)
        elif type_.lower() == "problem":
            searchable_text = self.searchable_text_from_problem_data(mongo_module)
        elif type_.lower() == "transcript":
            searchable_text = self.find_transcript_for_video_module(mongo_module)
        return searchable_text

    def get_thumbnail(self, mongo_module, type_):
        """
        General interface for getting an appropriate thumbnail for a given mongo module

        Currently the only types of modules supported ar pdfs, problems, and transcripts
        """
        if type_.lower() == "pdf":
            try:
                name = re.sub(r'(.*?)(/asset/)(.*?)(\.pdf)(.*?)$', r'\3' + ".pdf", mongo_module["definition"]["data"])
                asset = self.find_asset_with_name(name)
                if asset is None:
                    raise DelegateError
                thumbnail = self.thumbnail_from_pdf(asset.get("data", "").__str__())
            except (DelegateError, MissingDelegateError, CorruptImageError):
                thumbnail = ""
        elif type_.lower() == "problem":
            thumbnail = self.thumbnail_from_html(mongo_module["definition"]["data"])
        elif type_.lower() == "transcript":
            thumbnail = self.thumbnail_from_video_module(mongo_module)
        return thumbnail

    def index_all_pdfs(self, index, bulk_chunk=5):
        """
        Indexes all pdfs.

        For some reason pdfs are currently represented as html modules with references to pdfs,
        as such this might seem a little hacky, but it's largely an artefact of the underlying data.
        """
        cursor = self.find_categories_with_regex("html", re.compile(r".*?/asset/.*?\.pdf.*?"))
        bulk_string = ""
        for i in range(cursor.count()):
            item = cursor.next()
            data = self.basic_dict(item, "pdf")
            bulk_string += json.dumps({"index": {"_index": index, "_type": data["type_hash"], "_id": data["hash"]}})
            bulk_string += "\n"
            bulk_string += json.dumps(data)
            bulk_string += "\n"
            if i % bulk_chunk == 0:
                log.debug(i)
                self.es_instance.bulk_index(bulk_string)
                bulk_string = ""
        self.es_instance.bulk_index(bulk_string)

    def index_all_problems(self, index, bulk_chunk=100):
        """
        Similar to index_all_pdfs, but our storage of problems is more sensical.
        """
        cursor = self.find_modules_by_category("problem")
        bulk_string = ""
        for i in range(cursor.count()):
            item = cursor.next()
            print i
            try:
                data = self.basic_dict(item, "problem")
            except IOError:  # In case the connection is refused for whatever reason, try again
                data = self.basic_dict(item, "problem")
            bulk_string += json.dumps({"index": {"_index": index, "_type": data["type_hash"], "_id": data["hash"]}})
            bulk_string += "\n"
            bulk_string += json.dumps(data)
            bulk_string += "\n"
            if i % bulk_chunk == 0:
                log.debug(i)
                self.es_instance.bulk_index(bulk_string)
                bulk_string = ""
        self.es_instance.bulk_index(bulk_string)

    def index_all_transcripts(self, index, bulk_chunk=100):
        """
        Similar to two the other two index_all methods.

        This is arguably the hackiest of all since our storage of transcripts as separate static files
        that aren't directly linked to the video is both different from how everything else is stored,
        and not very advantageous seeing as transcripts are tiny.
        """

        cursor = self.find_modules_by_category("video")
        bulk_string = ""
        for i in range(cursor.count()):
            item = cursor.next()
            try:
                data = self.basic_dict(item, "transcript")
            except IOError:  # In case the connection is refused for whatever reason, try again
                data = self.basic_dict(item, "transcript")
            bulk_string += json.dumps({"index": {"_index": index, "_type": data["type_hash"], "_id": data["hash"]}})
            bulk_string += "\n"
            bulk_string += json.dumps(data)
            bulk_string += "\n"
            if i % bulk_chunk == 0:
                log.debug(i)
                self.es_instance.bulk_index(bulk_string).content
                bulk_string = ""
        self.es_instance.bulk_index(bulk_string).content

    def index_course(self, course):
        """
        Indexes all of the searchable content for a course
        """

        cursor = self.find_modules_for_course(course)
        for _ in range(cursor.count()):
            item = cursor.next()
            category = item["_id"]["category"].lower().strip()
            data = {}
            index = ""
            if category == "video":
                data = self.basic_dict(item, "transcript")
                index = "transcript-index"
            elif category == "problem":
                data = self.basic_dict(item, "problem")
                index = "problem-index"
            elif category == "html":
                pattern = re.compile(r".*?/asset/.*?\.pdf.*?")
                if pattern.match(item["definition"]["data"]):
                    data = self.basic_dict(item, "pdf")
                else:
                    data = {"test": ""}
                index = "pdf-index"
            else:
                continue
            if filter(None, data.values()) == data.values():
                print self.es_instance.index_data(index, item["_id"]["course"], data, data["hash"]).content


class PyGrep:
    """
    Just a small utility that was useful for getting transcripts from a file system.

    This was mostly used for the xml courses and so it isn't super relevant any more, but
    it has enough simple utility to make it worthwhile in case similar things pop up in the future
    """

    def __init__(self, directory):
        """
        Just specifies the root directory to search through.
        """

        self.directory = directory

    def grab_all_files_with_ending(self, file_ending):
        """
        Will return absolute paths to all files with given file ending in self.directory
        """

        walk_results = os.walk(self.directory)
        file_check = lambda walk: len(walk[2]) > 0
        ending_prelim = lambda walk: file_ending in " ".join(walk[2])
        relevant_results = (entry for entry in walk_results if file_check(entry) and ending_prelim(entry))
        return (self.grab_files_from_os_walk(result, file_ending) for result in relevant_results)

    def grab_files_from_os_walk(self, os_walk_tuple, file_ending):
        """
        Returns the actual files from os.walk results.
        """

        format_check = lambda file_name: file_ending in file_name
        directory, _, file_paths = os_walk_tuple
        return [os.path.join(directory, file_path) for file_path in file_paths if format_check(file_path)]
