"""
Mocking/testing utils for ESG
"""
import json

from os import path


DATA_ROOT = "/edx/app/edxapp/edx-platform/lms/djangoapps/ora_staff_grader/mock/data"

def read_data_file(file_name):
    """ Return data from a JSON file in the /data dir """
    with open(path.join(DATA_ROOT, file_name), "r") as data_file:
        return json.load(data_file)

def get_course_metadata(course_id):
    return read_data_file("course_metadata.json")[course_id]

def get_ora_metadata(ora_location):
    return read_data_file("ora_metadata.json")[ora_location]

def get_submissions(ora_location):  # pylint: disable=unused-argument
    return read_data_file("submissions.json")
