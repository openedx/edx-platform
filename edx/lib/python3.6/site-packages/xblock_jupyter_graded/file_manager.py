from contextlib import contextmanager
import json
import logging
import os
import pkg_resources
import nbformat
import shutil
import tempfile

from exceptions import ValidationError
from config import (
    RELEASE, SUBMITTED, SOURCE, AUTOGRADED, FEEDBACK, EDX_ROOT
)

log = logging.getLogger(__name__)


def create_autograded_dir(course_id, unit_id, username):
    """Creates autograded dir on EdX"""
    path = os.path.join(EDX_ROOT, course_id, AUTOGRADED, username, unit_id)
    if not os.path.exists(path):
        os.makedirs(path)


def create_feedback_dir(course_id, unit_id, username):
    """Creates feedback dir on EdX"""
    path = os.path.join(EDX_ROOT, course_id, FEEDBACK, username, unit_id)
    if not os.path.exists(path):
        os.makedirs(path)


def create_course_dirs(course_id):
    """Creates base nbgrader course directories if they don't exist"""
    if os.path.exists(os.path.join(EDX_ROOT, course_id)):
        return

    release_path = os.path.join(EDX_ROOT, course_id, RELEASE)
    os.makedirs(release_path)
    log.info("Created Path(s): {}".format(release_path))

    submitted_path = os.path.join(EDX_ROOT, course_id, SUBMITTED)
    os.mkdir(submitted_path)
    log.info("Created Path: {}".format(submitted_path))

    source_path = os.path.join(EDX_ROOT, course_id, SOURCE)
    os.mkdir(source_path)
    log.info("Created Path: {}".format(source_path))

    fb_path = os.path.join(EDX_ROOT, course_id, FEEDBACK)
    os.mkdir(fb_path)
    log.info("Created Path: {}".format(fb_path))


def save_instructor_nb(course_id, unit_id, f):
    """Saves instructor notebook in course_id/SOURCE/unit_id/"""
    if not os.path.exists(os.path.join(EDX_ROOT, course_id, SOURCE, unit_id)):
        os.makedirs(os.path.join(EDX_ROOT, course_id, SOURCE, unit_id))

    nb_path = os.path.join(EDX_ROOT, course_id, SOURCE, unit_id, f.filename)
    with open(nb_path, "w") as nb:
        nb.write(f.file.read())

    log.info("Wrote file: {}".format(nb_path))


def save_student_nb(username, course_id, unit_id, f):
    """Saves student notebook in course_id/username/SUBMITTED/unit_id/"""
    student_path = os.path.join(EDX_ROOT, course_id, SUBMITTED, username, unit_id)
    if not os.path.exists(student_path):
        os.makedirs(student_path)

    nb_path = os.path.join(EDX_ROOT, course_id, SUBMITTED, username, unit_id, f.filename)
    with open(nb_path, "w") as nb:
        nb.write(f.file.read())

    log.info("Wrote file: {}".format(nb_path))


def validate_instructor_nb(nb_file):
    """Ensures there is at least one BEGIN SOLUTION TAG in uploaded nb
    
    Should prevent accidentally uploading a student NB
    """
    
    solution_text = "BEGIN SOLUTION"
    found = False

    raw = nb_file.file.read()
    nb_file.file.seek(0)

    try:
        # TODO: as_verion = 4? should this come from the nb somehow?
        nb = nbformat.reads(raw, as_version=4)

    except Exception as e:
        log.exception(e)
        raise ValidationError(str(e))

    for cell in nb['cells']:
        if solution_text in cell['source']:
            log.info("Found solution cell")
            return

    raise ValidationError("No Solution Cells Found in uploaded notebook!"\
            " Are you sure this is the instructor version?")
    

@contextmanager
def create_temp_config(config_lines):
    """Creates a temp nbgrader_config like file from `config_lines` list
    
    File is removed when context manager exits.

    Each `config_lines` list entry should look like an nbgrader_config.py 
    line without the leading `c`. 
    
    Examples: 
        ExecutePreprocessor.timeout = 5
        ClearSolutions.text_stub = 'PUT YOUR ANSWER HERE'
    """
    fd = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    fd.write("c = get_config()\n")
    fd.write("c.ExecutePreprocessor.kernel_name = 'temp_env'\n")
    for line in config_lines:
        fd.write("c.{}\n".format(line))
    fd.close()

    yield fd.name

    if os.path.exists(fd.name):
        os.remove(fd.name)
        log.info("removed temp config file: {}".format(fd.name))
    else:
        log.warning("Temp config file: {} did not exist".format(fd.name))


        



    

