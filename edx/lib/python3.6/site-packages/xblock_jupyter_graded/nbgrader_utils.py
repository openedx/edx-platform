import json
import logging 
import os
import pkg_resources
from subprocess import Popen, PIPE

from config import (
    RELEASE, SUBMITTED, SOURCE, AUTOGRADED, FEEDBACK, EDX_ROOT, CONT_ROOT
)
import file_manager as fm
import container_manager as cm
from exceptions import DockerContainerError, ValidationError

log = logging.getLogger(__name__)


def normalize_course_id(course_id):
    """Make course_id directory naming name worthy
    
    convert: 
        from: course-v1:course+name
        to: course_name
        """
    return course_id.split(":")[1].replace("+", "_")


def normalize_unit_id(unit_id):
    """Make unit_id directory name worthy
    
    convert: 
        from: block-v1:course+type@vertical+block@digits 
        to: vertical_block_digits
        """
    return "_".join(unit_id.split("@")[1:]).replace("+", "_")


def init_new_course(course_id):
    """Create edx directory structure for new course"""
    fm.create_course_dirs(course_id)


def generate_student_nb(course_id, unit_id, f):
    """Runs nbgrader assign and returns max possible notebook score"""
    course = normalize_course_id(course_id)
    unit = normalize_unit_id(unit_id)

    # Create new course structure if necessary
    init_new_course(course)

    # Validate and Save instructor source notebook
    fm.validate_instructor_nb(f)
    fm.save_instructor_nb(course, unit, f)

    max_score = _run_assign_container(f.filename, course, unit)

    return max_score


def autograde_notebook(username, course_id, unit_id, f, cell_timeout=15, allow_net=False):
    """Runs nbgrader autograde and returns student score
    
    Requires normalized course_id/unit_id
    """

    course = normalize_course_id(course_id)
    unit = normalize_unit_id(unit_id)

    fm.save_student_nb(username, course, unit, f)
    score = _run_autograde_container(f.filename, course, unit, username, cell_timeout, allow_net)
    return score


def _run_assign_container(nb_filename, course_id, unit_id):
    """Runs assign to generate student nb and returns max score

    Requires normalized course_id/unit_id
    """

    build_container_if_not_exists(course_id)

    host_source_path = os.path.join(EDX_ROOT, course_id, SOURCE, unit_id)
    cont_source_path = os.path.join(CONT_ROOT, SOURCE, 'ps1')
    host_release_path = os.path.join(EDX_ROOT, course_id, RELEASE, unit_id)
    cont_release_path = os.path.join(CONT_ROOT, RELEASE, 'ps1')

    cmd = [
        'sudo', '-u', 'jupyter', 'docker', 'run', '-t',
        '-v', "{}:{}".format(host_source_path, cont_source_path),
        '-v', "{}:{}".format(host_release_path, cont_release_path),
        course_id.lower(), 'python', '/home/jupyter/run_grader.py', 
        '--cmd', 'assign',
        '--nbname', nb_filename,
    ]
    p = Popen(cmd, stderr=PIPE, stdout=PIPE)
    out, err = p.communicate()

    if p.returncode != 0:
        raise DockerContainerError(err.decode('utf-8'));

    nb_name = os.path.splitext(nb_filename)[0]
    result_fn = "{}_results.json".format(nb_name)
    with open(os.path.join(host_release_path, result_fn), 'r') as f:
        results = json.load(f)

    if not results['success']:
        raise DockerContainerError(results['err'])
    return results['max_score']


def _run_autograde_container(nb_filename, course_id, unit_id, username, 
        cell_timeout, allow_net):
    """Runs autograde for notebook and student, returning student score
    
    Requires normalized course_id/unit_id
    """
    # Create student based directories 
    fm.create_autograded_dir(course_id, unit_id, username)
    fm.create_feedback_dir(course_id, unit_id, username)

    # Create host:container directory mappings
    host_source_path = os.path.join(EDX_ROOT, course_id, SOURCE, unit_id, nb_filename)
    cont_source_path = os.path.join(CONT_ROOT, SOURCE, 'ps1', nb_filename)

    host_submitted_path = os.path.join(EDX_ROOT, course_id, SUBMITTED, username, unit_id, nb_filename)
    cont_submitted_path = os.path.join(CONT_ROOT, SUBMITTED, username, 'ps1', nb_filename)

    host_autograded_path = os.path.join(EDX_ROOT, course_id, AUTOGRADED, username, unit_id)
    cont_autograded_path = os.path.join("/{}".format(AUTOGRADED))

    host_fb_path = os.path.join(EDX_ROOT, course_id, FEEDBACK, username, unit_id)
    cont_fb_path = os.path.join("/{}".format(FEEDBACK))

    # Set cell timeout config option
    # NOTE: Could expand to set other nbgrader settings here
    config = ["ExecutePreprocessor.timeout = {}".format(cell_timeout)]

    # Create a temp config file and map it into the container
    # NOTE: Could allow for notebook specific settings instead of XBlock wide
    with fm.create_temp_config(config) as filename:
        host_config_path = filename
        cont_config_path = os.path.join("/etc", "jupyter", "nbgrader_config.py")

        cmd = [
            'sudo', '-u', 'jupyter', 'docker', 'run', '-t',
            '-v', "{}:{}:ro".format(host_source_path, cont_source_path),
            '-v', "{}:{}:ro".format(host_submitted_path, cont_submitted_path),
            '-v', "{}:{}".format(host_autograded_path, cont_autograded_path),
            '-v', "{}:{}".format(host_fb_path, cont_fb_path),
            '-v', "{}:{}:ro".format(host_config_path, cont_config_path)
        ]

        # Optionally disable all network access
        if not allow_net:
            log.info("Disabling network access from docker container")
            cmd += ['--network', 'none']

        cmd += [
            course_id.lower(), 'python', '/home/jupyter/run_grader.py', 
            '--cmd', 'grade',
            '--nbname', nb_filename,
            '--username', username,
        ]
        
        p = Popen(cmd, stderr=PIPE, stdout=PIPE)
        out, err = p.communicate()

        if p.returncode != 0:
            raise DockerContainerError(err.decode('utf-8'));

    # Get and read results
    nb_name = os.path.splitext(nb_filename)[0]
    result_fn = "{}_results.json".format(nb_name)
    with open(os.path.join(host_autograded_path, result_fn), 'r') as f:
        results = json.load(f)
    
    if not results['success']:
        raise DockerContainerError(results['err'])
    return {
        'total': results['total_score'],
        'section_scores': results['section_scores'],
        'autograded_err': results['autograded_err']
    }
    

def update_requirements(course_id, f):
    """Updates Requirements model file this course_id"""
    course = normalize_course_id(course_id)
    try:
        packages = f.file.readlines() 
    except AttributeError:
        raise ValidationError("No File Attached")
    manager = cm.ContainerManager(course)
    manager.set_requirements(packages)
    manager.build_container()
    manager.cleanup()


def get_requirements(course_id):
    """Returns contents of current requirements.txt for `course`"""
    course = normalize_course_id(course_id)
    manager = cm.ContainerManager(course)
    return manager.get_package_list()


def build_container_if_not_exists(course_id):
    """Builds the docker container if it doesn't exist

    Requires normalized course_id
    """
    manager = cm.ContainerManager(course_id)
    if not manager.container_exists():
        log.info("Containter: {} did not exist, building...".format(course_id))
        manager.build_container()
        manager.cleanup()



