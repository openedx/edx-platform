"""
General methods and classes for interaction with the Mongo Database and Elasticsearch instance
"""

import os
import re
import hashlib
import logging
from itertools import chain

import json
import requests
import lxml.html
from requests.exceptions import RequestException
from django.conf import settings
from pymongo import MongoClient

log = logging.getLogger(__name__)
MONGO_COURSE_CACHE = {}

"""
For ElasticSearch's bulk indexing we define a chunk size which is how many documents we will send at once.

The current number is arbitrary, but the goal is to reduce the number of network requests, and stay robust
against having a single malformed field.

10 is a pretty decent middle ground.
"""

CHUNK_SIZE = 10


def flaky_request(method, url, attempts=2, **kwargs):
    """
    General exception handling for requests
    """

    for _ in range(attempts):
        try:
            return requests.request(method, url, **kwargs)
        except RequestException:
            pass
    return None


class MalformedDataException(Exception):
    """
    Basic Exception raised whenever searchable text cannot be found for an object
    """

    pass


class ElasticDatabase(object):
    """
    A wrapper for Elastic Search that sits on top of the existent REST api.

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
            settings_file = os.path.join(current_directory, "settings.json")

        with open(settings_file) as source:
            self.index_settings = json.load(source)

    def index_data(self, index, data, type_, id_):
        """
        Actually indexes given data at the indicated type and id.

        If no type or id is provided, this will assume that the type and id are
        contained within the data object passed to the index_data function in the
        hash and type_hash fields.

        Data should be a dictionary that matches the mapping of the given type.
        """

        full_url = "/".join([self.url, index, type_, id_])
        return flaky_request("post", full_url, data=json.dumps(data))

    def bulk_index(self, all_data):
        """
        Allows for bulk indexing of properly formatted json strings.
        Example:
        {"index": {"_index": "transcript-index", "_type": "course_hash", "_id": "id_hash"}}
        {"field1": "value1"...}

        Important: Bulk indexing is newline delimited, make sure newlines are only
        between action (line starting with index) and data (line starting with field1)
        """

        url = self.url + "/_bulk"
        return flaky_request("post", url, data=all_data)


class MongoIndexer(object):
    """
    This class is the connection point between Mongo and ElasticSearch.
    """

    def __init__(self, es_instance=ElasticDatabase()):
        host = settings.MODULESTORE['default']['OPTIONS']['host']
        port = 27017
        client = MongoClient(host, port)
        content_db = settings.CONTENTSTORE["OPTIONS"]['db']
        module_db = settings.MODULESTORE['default']['OPTIONS']['db']
        self._chunk_collection = client[content_db]["fs.chunks"]
        self._module_collection = client[module_db]["modulestore"]
        self._es_instance = es_instance

    def _get_bulk_index_item(self, index, data):
        """
        Returns a string representing the next indexing action for bulk index

        Format example is in the doc string for bulk_index. Reposted here for clarity:
        Example:
        {"index": {"_index": "transcript-index", "_type": "course_hash", "_id": "id_hash"}}
        {"field1": "value1"...}
        """

        return_string = ""
        return_string += json.dumps({"index": {"_index": index, "_type": data["type_hash"], "_id": data["hash"]}})
        return_string += "\n"
        return_string += json.dumps(data)
        return_string += "\n"
        return return_string

    def _get_course_name_from_mongo_module(self, mongo_module):
        """
        Given a mongo_module, returns the name for the course element it belongs to
        """
        course_element = self._module_collection.find_one({
            "_id.course": mongo_module["_id"]["course"],
            "_id.category": "course"
        })
        return course_element["_id"]["name"]

    def _get_uuid_from_video_module(self, video_module):
        """
        Returns the youtube uuid given a video module.

        Implementation right now is a little hacky since we don't actually have a specific
        value for the relevant uuid, though we implicitly refer to all videos by their 1.0
        speed youtube uuids throughout the database.

        Example of the data associated with a video_module:

        <video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">
        """

        data = video_module.get("definition", {}).get("data", "")
        if isinstance(data, dict):
            data = data.get("data", "")
        if "1.0" in data:
            uuids = data.split(",")
            # In the case that we get a value that has any extra information past its closing
            # quotation, it should be stripped to ensure a valid uuid
            subtract_suffix = lambda word: word[:word.rfind("\"")] if "\"" in word else word
            # The colon is kind of a hack to make sure there will always be a second element since
            # some entries don't have a second entry
            # Example: <video youtube="1.0:uuid,1.50, someother_metadata"/>
            speed_map = {(entry + ":").split(":")[0]: (entry + ":").split(":")[1] for entry in uuids}
            uuid = [subtract_suffix(value) for key, value in speed_map.items() if "1.0" in key]
            if not uuid:
                raise MalformedDataException
            return uuid[0]
        else:
            raise MalformedDataException

    def _get_thumbnail_from_video_module(self, video_module):
        """
        Return an appropriate binary thumbnail for a given video module
        """

        data = video_module.get("definition", {}).get("data", "")
        if "player.youku.com" in data:
        # Some videos use the youku player, this is just the default youku icon
        # Youku requires an api key to pull down relevant thumbnails, but
        # if that is ever present this should be switched. Right now it only applies to two videos.
            return "https://lh6.ggpht.com/8_h5j6hiFXdSl5atSJDf8bJBy85b3IlzNWeRzOqRurfNVI_oiEG-dB3C0vHRclOG8A=w170"
        else:
            uuid = self._get_uuid_from_video_module(video_module)
            if uuid is None:
                return "http://img.youtube.com"
            else:
                return "http://img.youtube.com/vi/%s/0.jpg" % uuid

    def _get_thumbnail_from_html(self, html):
        """
        extracts the first image from the problem if there is an image present

        Otherwise there will be no thumbnail for the problem
        """

        html_document = lxml.html.fromstring(html)
        images = html_document.cssselect('img')
        if len(images) > 0:
            return images[0].attrib['src']
        else:
            return ""

    def _get_searchable_text_from_problem_data(self, mongo_element):
        """
        Returns some fascimile of searchable text from a mongo problem element

        The data field from the problem is in weird xml, which is good for functionality, but bad for search
        """

        data = mongo_element["definition"]["data"]
        # Grabs all text in paragraph tags.
        paragraphs = [text for text in re.findall(r"<p>(.*?)</p>", data)]
        # Grabs all text between text tags, which is the most common container after paragraph tags.
        text_groups = [text for text in re.findall(r"<text>(.*?)</text>", data)]
        full_text = "%s %s" % (" ".join(paragraphs), " ".join(text_groups))
        # This gets rid of things like latex strings and other non-human readable escaped passages
        cleaned_text = re.sub(r"\\(.*?\\)", "", full_text).replace("\\", "")
        # Removes all lingering tags
        remove_tags = re.sub(r"<[a-zA-Z0-9/\.\= \"\'_-]+>", "", cleaned_text)
        if not remove_tags.strip():
            raise MalformedDataException
        return remove_tags

    def _find_transcript_for_video_module(self, video_module):
        """
        Returns a transcript for a video given the module that contains it.

        The video module should be passed in as an element from some mongo cursor.
        """

        data = video_module.get("definition", {}).get("data", "")
        if isinstance(data, dict):  # For some reason there are nested versions
            data = data.get("data", "")
        if isinstance(data, unicode) is False:  # for example videos
            raise MalformedDataException
        uuid = self._get_uuid_from_video_module(video_module)
        name_pattern = re.compile(".*" + uuid + ".*")
        chunk = (
            self._chunk_collection.find_one({"files_id.name": name_pattern})
        )
        if chunk is None:
            raise MalformedDataException
        else:
            try:
                chunk_data = chunk["data"].decode('utf-8')
                if "com.apple.quar" in chunk_data:
                    # This seemingly arbitrary error check brought to you by apple.
                    # This is an obscure, barely documented occurance where apple broke tarballs
                    # and decided to shove error messages into tar metadata which causes this.
                    # https://discussions.apple.com/thread/3145071?start=0&tstart=0
                    raise MalformedDataException
                else:
                    try:
                        return " ".join(filter(None, json.loads(chunk_data)["text"]))
                    except ValueError:
                        log.error("Transcript for: " + uuid + " is invalid")
                        return chunk_data
            except UnicodeError:
                raise MalformedDataException

    def _get_searchable_text(self, mongo_module, type_):
        """
        Returns searchable text for a module. Defined for a module only
        """

        if type_.lower() == "problem":
            return self._get_searchable_text_from_problem_data(mongo_module)
        elif type_.lower() == "transcript":
            return self._find_transcript_for_video_module(mongo_module)
        else:
            log.error("%s is not a recognized type" % type_)
            raise NotImplementedError

    def _get_thumbnail(self, mongo_module, type_):
        """
        General interface for getting an appropriate thumbnail for a given mongo module

        Currently the only types of modules supported are problems, and transcripts
        """

        if type_.lower() == "problem":
            return self._get_thumbnail_from_html(mongo_module["definition"]["data"])
        elif type_.lower() == "transcript":
            return self._get_thumbnail_from_video_module(mongo_module)
        else:
            log.error("%s is not a recognized type" % type_)
            raise NotImplementedError

    def _get_full_dict(self, mongo_module, type_):
        """
        Returns the part of the es schema that is the same for every object.
        """

        id_ = json.dumps(mongo_module["_id"])
        org = mongo_module["_id"]["org"]
        course = mongo_module["_id"]["course"]
        if not MONGO_COURSE_CACHE.get(course, False):
            MONGO_COURSE_CACHE[course] = self._get_course_name_from_mongo_module(mongo_module)
        run = MONGO_COURSE_CACHE[course]

        course_id = "/".join([org, course, run])
        log.debug(course_id)
        item_hash = hashlib.sha1(id_).hexdigest()
        display_name = (
            mongo_module.get("metadata", {}).get("display_name", "") +
            " (" + mongo_module["_id"]["course"] + ")"
        )
        searchable_text = self._get_searchable_text(mongo_module, type_)
        thumbnail = self._get_thumbnail(mongo_module, type_)
        type_hash = hashlib.sha1(course_id).hexdigest()
        return {
            "id": id_,
            "hash": item_hash,
            "display_name": display_name,
            "course_id": course_id,
            "searchable_text": searchable_text,
            "thumbnail": thumbnail,
            "type_hash": type_hash
        }

    def _find_modules_for_course(self, course):
        """
        Returns a cursor matching all modules in the given course
        """

        cursor = self._module_collection.find({"_id.course": course}, timeout=False)
        # Pymongo's cursors are a little finnicky, so this is just explicitly casting it to a standard generator
        return (entry for entry in chain(cursor))

    def index_course(self, course):
        """
        Indexes all of the searchable content for a course
        """

        cursor = self._find_modules_for_course(course)
        counter = 0
        index_string = ""
        error_string = ""
        for item in cursor:
            category = item["_id"]["category"].lower().strip()
            data = {}
            index = ""
            try:
                if category == "video":
                    data = self._get_full_dict(item, "transcript")
                    index = "transcript-index"
                elif category == "problem":
                    data = self._get_full_dict(item, "problem")
                    index = "problem-index"
                else:
                    continue
            except MalformedDataException:
                continue
            index_string += self._get_bulk_index_item(index, data)
            error_string += item["_id"]["name"] + "\n"
            counter += 1
            if counter % CHUNK_SIZE == 0:
                index_status_code = self._es_instance.bulk_index(index_string).status_code
                if index_status_code == 400:
                    log.error("The following bulk index failed: %s" % error_string)
                index_string = ""
                error_string = ""
