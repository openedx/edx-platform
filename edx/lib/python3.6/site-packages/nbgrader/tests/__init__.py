import os
import glob
import shutil
import subprocess as sp
import sys
import logging
import warnings
import socket

from six import StringIO
from nbformat.v4 import new_code_cell, new_markdown_cell
from jupyter_core.application import NoStart
from nbconvert.filters import strip_ansi

from ..utils import compute_checksum
from ..apps.nbgraderapp import NbGraderApp
from ..validator import Validator


def create_code_cell():
    source = """print("something")
### BEGIN SOLUTION
print("hello")
### END SOLUTION"""
    cell = new_code_cell(source=source)
    return cell


def create_text_cell():
    source = "this is the answer!\n"
    cell = new_markdown_cell(source=source)
    return cell


def create_grade_cell(source, cell_type, grade_id, points, schema_version=1):
    if cell_type == "markdown":
        cell = new_markdown_cell(source=source)
    elif cell_type == "code":
        cell = new_code_cell(source=source)
    else:
        raise ValueError("invalid cell type: {}".format(cell_type))

    cell.metadata.nbgrader = {}
    cell.metadata.nbgrader["grade"] = True
    cell.metadata.nbgrader["grade_id"] = grade_id
    cell.metadata.nbgrader["points"] = points
    cell.metadata.nbgrader["solution"] = False
    cell.metadata.nbgrader["locked"] = False
    cell.metadata.nbgrader["schema_version"] = schema_version

    return cell


def create_solution_cell(source, cell_type, grade_id, schema_version=1):
    if cell_type == "markdown":
        cell = new_markdown_cell(source=source)
    elif cell_type == "code":
        cell = new_code_cell(source=source)
    else:
        raise ValueError("invalid cell type: {}".format(cell_type))

    cell.metadata.nbgrader = {}
    cell.metadata.nbgrader["solution"] = True
    cell.metadata.nbgrader["grade_id"] = grade_id
    cell.metadata.nbgrader["grade"] = False
    cell.metadata.nbgrader["locked"] = False
    cell.metadata.nbgrader["schema_version"] = schema_version

    return cell


def create_locked_cell(source, cell_type, grade_id, schema_version=1):
    if cell_type == "markdown":
        cell = new_markdown_cell(source=source)
    elif cell_type == "code":
        cell = new_code_cell(source=source)
    else:
        raise ValueError("invalid cell type: {}".format(cell_type))

    cell.metadata.nbgrader = {}
    cell.metadata.nbgrader["locked"] = True
    cell.metadata.nbgrader["grade_id"] = grade_id
    cell.metadata.nbgrader["solution"] = False
    cell.metadata.nbgrader["grade"] = False
    cell.metadata.nbgrader["schema_version"] = schema_version

    return cell


def create_grade_and_solution_cell(source, cell_type, grade_id, points, schema_version=1):
    if cell_type == "markdown":
        cell = new_markdown_cell(source=source)
    elif cell_type == "code":
        cell = new_code_cell(source=source)
    else:
        raise ValueError("invalid cell type: {}".format(cell_type))

    cell.metadata.nbgrader = {}
    cell.metadata.nbgrader["solution"] = True
    cell.metadata.nbgrader["grade"] = True
    cell.metadata.nbgrader["grade_id"] = grade_id
    cell.metadata.nbgrader["points"] = points
    cell.metadata.nbgrader["locked"] = False
    cell.metadata.nbgrader["schema_version"] = schema_version

    return cell


def start_subprocess(command, **kwargs):
    kwargs['env'] = kwargs.get('env', os.environ.copy())
    proc = sp.Popen(command, **kwargs)
    return proc


def copy_coverage_files():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    if os.getcwd() != root:
        coverage_files = glob.glob(".coverage.*")
        if len(coverage_files) == 0 and 'COVERAGE_PROCESS_START' in os.environ:
            warnings.warn("No coverage files produced")
        for filename in coverage_files:
            shutil.copyfile(filename, os.path.join(root, filename))


def run_command(command, retcode=0, coverage=True, **kwargs):
    proc = start_subprocess(command, stdout=sp.PIPE, stderr=sp.STDOUT, **kwargs)
    output = proc.communicate()[0].decode()
    output = output.replace("Coverage.py warning: No data was collected.\n", "")
    print(output)

    true_retcode = proc.poll()
    if true_retcode != retcode:
        raise AssertionError(
            "process returned an unexpected return code: {}".format(true_retcode))

    if coverage:
        copy_coverage_files()

    return output


def run_nbgrader(args, retcode=0, env=None, stdout=False):
    # store os.environ
    old_env = os.environ.copy()
    if env:
        os.environ = env

    # create the application
    app = NbGraderApp.instance()

    # hook up buffers for getting log output or stdout/stderr
    if not stdout:
        log_buff = StringIO()
    else:
        stdout_buff = StringIO()
        orig_stdout = sys.stdout
        sys.stdout = stdout_buff
        Validator.stream = stdout_buff

    try:
        app.initialize(args)
        if not stdout:
            app.init_logging(logging.StreamHandler, [log_buff], color=False, subapps=True)
        app.start()
    except NoStart:
        true_retcode = 0
    except SystemExit as e:
        true_retcode = e.code
    else:
        true_retcode = 0
    finally:
        # get output
        if not stdout:
            out = log_buff.getvalue()
            log_buff.close()
        else:
            out = stdout_buff.getvalue()
            stdout_buff.close()
            sys.stdout = orig_stdout
            Validator.stream = orig_stdout

        # reset application state
        app.reset()

        # restore os.environ
        os.environ = old_env

    if retcode != true_retcode:
        raise AssertionError(
            "process returned an unexpected return code: {}".format(true_retcode))

    return out


def get_free_ports(n):
    """Based on https://gist.github.com/dbrgn/3979133"""
    ports = []
    sockets = []
    for i in range(n):
        s = socket.socket()
        s.bind(('', 0))
        port = s.getsockname()[1]
        ports.append(port)
        sockets.append(s)
    for s in sockets:
        s.close()
    return ports
