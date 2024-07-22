import logging
import json
import pytz

from bson.json_util import dumps
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from common.djangoapps.util.json_request import JsonResponse
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from django.views.decorators.clickjacking import xframe_options_exempt
from itertools import chain


log = logging.getLogger(__name__)



def get_course_unit_log(course_id):
    course_key = CourseKey.from_string(course_id)
    split_modulestore = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.split)
    active_version_collection = split_modulestore.db_connection.course_index
    structure_collection = split_modulestore.db_connection.structures
    course_definition = active_version_collection.find({"org" : course_key.org, "course" : course_key.course, "run" : course_key.run})

    published_version  = structure_collection.find_one({"_id" : course_definition[0]["versions"]["published-branch"]})

    #fetch all previous versions
    all_previous_versions = [] 
    document = published_version

    while True:
        previous_version_id = document["previous_version"]
        document = structure_collection.find_one({"_id": previous_version_id})

        if not document:
            break

        all_previous_versions.append(document)

    all_previous_versions = sorted(all_previous_versions, key=lambda x: x.get("edited_on", 0))

    data = get_course_history(course_definition, published_version, all_previous_versions)    
    return data


def get_course_history(course_definition, published_version, all_previous_versions):
    course_logs = {"last_updated_on" : conver_utc_ist(published_version["edited_on"]), 
            "components" : {}, "section_details" : {}, "subsection_details" : {}, "unit_details" : {}}

    course_logs["latest_published_componenets"] = [block["block_id"] for block in published_version["blocks"] if block["block_type"] not in ("course", "course_info", "about",  "chapter", "vertical", "sequential")]

    for version in all_previous_versions:
        course_logs = process_course_logs(version, course_logs)

    course_logs = process_course_logs(published_version, course_logs)

    return course_logs

def process_course_logs(version, course_logs):

    components_list = []

    for block in version["blocks"]:

        if block["block_type"] not in ("course", "course_info", "about",  "chapter", "vertical", "sequential", "static_tab"):
            block_id = block["block_id"]

            components_list.append(block_id)

            parents_list, parents_names = find_block_parents(version, block_id)

            edited_on = conver_utc_ist(block['edit_info']['edited_on'])
            user_obj = User.objects.get(id = block["edit_info"]["edited_by"])

            if block_id not in course_logs["components"]:
                status = "Created"
                course_logs["components"][block_id] = {"block_type" : block["block_type"].replace("_"," ").title(), "edited_info" : []}

            else:

                previous_block_info = course_logs["components"][block_id]["edited_info"][-1]

                if block["definition"] != previous_block_info["definition"]:
                    status = "Edited"

                elif block["definition"] == previous_block_info["definition"] and previous_block_info["fields"] != block["fields"]:
                    status = "Edited"

                elif parents_list != previous_block_info["parents_list"]:
                    #add another obj as Moved Out with reference to -1 obj
                    course_logs["components"][block_id]["edited_info"].append({ "definition" : block["definition"], "fields" : block["fields"],
                                                                                "parents_list" : previous_block_info["parents_list"],
                                                                                "parents_names" : previous_block_info["parents_names"],
                                                                                "edited_on" : edited_on, "edited_by" : user_obj.first_name,
                                                                                "status" : "Moved Out"})
                    status = "Moved In"
                else:
                    continue

            course_logs["components"][block_id]["edited_info"].append({ "definition" : block["definition"], "fields" : block["fields"],
                                                                        "parents_list" : parents_list, "parents_names" : parents_names,
                                                                        "edited_on" : edited_on, "edited_by" : user_obj.first_name, 
                                                                        "status" : status})

    #Check for Deleted Blocks
    if components_list:
        deleted_blocks = list(set(course_logs["components"].keys()) - set(components_list))

        for d_block_id in deleted_blocks:
            previous_block_info = course_logs["components"][d_block_id]["edited_info"][-1]

            if previous_block_info["status"] != "Deleted" and d_block_id not in course_logs["latest_published_componenets"]: 
                user_obj = User.objects.get(id = version["edited_by"])
                course_logs["components"][d_block_id]["edited_info"].append({ "definition" : previous_block_info["definition"],
                                                                              "fields" : previous_block_info["fields"],
                                                                              "parents_list" : previous_block_info["parents_list"], 
                                                                              "parents_names" : previous_block_info["parents_names"],
                                                                              "edited_on" : conver_utc_ist(version["edited_on"]),
                                                                              "edited_by" : user_obj.first_name, "status" : "Deleted"})
    return course_logs

def find_block_parents(version, block_id):

    for block in version["blocks"]:
        if block["block_type"] == "vertical" and block_id in [i[-1] for i in block["fields"]["children"]]:
            unit_name = block["fields"]["display_name"]
            unit_id = block["block_id"]
            break

    for block in version["blocks"]:
        if block["block_type"] == "sequential" and unit_id in [i[-1] for i in block["fields"]["children"]]:
            subsection_name = block["fields"]["display_name"]
            subsection_id = block["block_id"]
            break

    for block in version["blocks"]:
        if block["block_type"] == "chapter" and subsection_id in [i[-1] for i in block["fields"]["children"]]:
            section_name = block["fields"]["display_name"]
            section_id = block["block_id"]
            break

    return [section_id, subsection_id, unit_id], [section_name, subsection_name, unit_name]


def conver_utc_ist(utc_datetime):
    utc_timezone = pytz.timezone('UTC')
    ist_timezone = pytz.timezone('Asia/Kolkata')
    edited_info_ist = utc_datetime.astimezone(ist_timezone)
    formated_ist = edited_info_ist.strftime("%b %d,%Y %H:%M:%S")
    return formated_ist

