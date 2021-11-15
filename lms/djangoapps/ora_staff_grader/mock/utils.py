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

def get_course_metadata(ora_location):
    """ Get course metadata, indexed by ORA block location """
    return read_data_file("course_metadata.json")[ora_location]

def get_ora_metadata(ora_location):
    """ Get ORA metadata, indexed by ORA block location """
    return read_data_file("ora_metadata.json")[ora_location]

def get_submissions(ora_location):  # pylint: disable=unused-argument
    """ Get Submission list, scoped by ORA block location """
    return read_data_file("submissions.json")[ora_location]

def fetch_submission(ora_location, submission_id):
    """ Fetch an individual submission, indexed first by ORA block location then Submission ID """
    return read_data_file("submissions.json")[ora_location].get(submission_id)

def fetch_default_response(submission_id):  # pylint: disable=unused-argument
    """ Return a default response, the same for all submissions """
    return read_data_file("responses.json").get("default")

def save_submission_update(submission):
    """ Update a submission key with new data """
    update_data_file("submissions.json", submission['submissionId'], submission)
