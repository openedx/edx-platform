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

def update_data_file(file_name, update_key, update_value):
    """ Update a single key/value within a JSON file """
    update_data = read_data_file(file_name)
    update_data[update_key] = update_value

    with open(path.join(DATA_ROOT, file_name), "w") as update_data_file:
        json.dump(update_data, update_data_file, indent=4)

def get_course_metadata(course_id):
    return read_data_file("course_metadata.json")[course_id]

def get_ora_metadata(ora_location):
    return read_data_file("ora_metadata.json")[ora_location]

def get_submissions(ora_location):  # pylint: disable=unused-argument
    return read_data_file("submissions.json")

def fetch_submission(submission_id):
    return read_data_file("submissions.json").get(submission_id)

def fetch_response(submission_id):  # pylint: disable=unused-argument
    # Right now, we use a single reponse
    return read_data_file("responses.json").get("default")

def save_submission_update(submission):
    """ Update a submission key with new data """
    update_data_file("submissions.json", submission['submissionId'], submission)
