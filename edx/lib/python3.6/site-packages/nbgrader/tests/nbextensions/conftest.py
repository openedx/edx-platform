import pytest
import tempfile
import os
import shutil
import subprocess as sp
import logging
import time
import sys
import signal
import glob

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from textwrap import dedent

from .. import copy_coverage_files, get_free_ports
from ...utils import rmtree


@pytest.fixture(scope="module")
def tempdir(request):
    tempdir = tempfile.mkdtemp()
    origdir = os.getcwd()
    os.chdir(tempdir)

    def fin():
        os.chdir(origdir)
        rmtree(tempdir)
    request.addfinalizer(fin)

    return tempdir


@pytest.fixture(scope="module")
def coursedir(request):
    tempdir = tempfile.mkdtemp()

    def fin():
        shutil.rmtree(tempdir)
    request.addfinalizer(fin)

    return tempdir


@pytest.fixture(scope="module")
def jupyter_config_dir(request):
    jupyter_config_dir = tempfile.mkdtemp()

    def fin():
        rmtree(jupyter_config_dir)
    request.addfinalizer(fin)

    return jupyter_config_dir

@pytest.fixture(scope="module")
def jupyter_data_dir(request):
    jupyter_data_dir = tempfile.mkdtemp()

    def fin():
        rmtree(jupyter_data_dir)
    request.addfinalizer(fin)

    return jupyter_data_dir


@pytest.fixture(scope="module")
def exchange(request):
    exchange = tempfile.mkdtemp()

    def fin():
        if os.path.exists(exchange):
            rmtree(exchange)
    request.addfinalizer(fin)

    return exchange


@pytest.fixture(scope="module")
def cache(request):
    cache = tempfile.mkdtemp()

    def fin():
        rmtree(cache)
    request.addfinalizer(fin)

    return cache


@pytest.fixture(scope="module")
def port():
    nbserver_port, = get_free_ports(1)
    return nbserver_port


def _make_nbserver(course_id, port, tempdir, jupyter_config_dir, jupyter_data_dir, exchange, cache):
    env = os.environ.copy()
    env['JUPYTER_CONFIG_DIR'] = jupyter_config_dir
    env['JUPYTER_DATA_DIR'] = jupyter_data_dir
    env['HOME'] = tempdir

    sp.check_call([sys.executable, "-m", "jupyter", "nbextension", "install", "--user", "--py", "nbgrader"], env=env)
    sp.check_call([sys.executable, "-m", "jupyter", "nbextension", "enable", "--user", "--py", "nbgrader"], env=env)
    sp.check_call([sys.executable, "-m", "jupyter", "serverextension", "enable", "--user", "--py", "nbgrader"], env=env)

    # create nbgrader_config.py file
    with open('nbgrader_config.py', 'w') as fh:
        fh.write(dedent(
            """
            c = get_config()
            c.Execute.execute_retries = 4
            c.CourseDirectory.db_assignments = [dict(name="Problem Set 1"), dict(name="ps.01")]
            c.CourseDirectory.db_students = [
                dict(id="Bitdiddle", first_name="Ben", last_name="B"),
                dict(id="Hacker", first_name="Alyssa", last_name="H"),
                dict(id="Reasoner", first_name="Louis", last_name="R")
            ]
            """
        ))

        if sys.platform != 'win32':
            fh.write(dedent(
                """
                c.Exchange.root = "{}"
                c.Exchange.cache = "{}"
                c.Exchange.course_id = "{}"
                """.format(exchange, cache, course_id)
            ))

    kwargs = dict(env=env)
    if sys.platform == 'win32':
        kwargs['creationflags'] = sp.CREATE_NEW_PROCESS_GROUP

    server = sp.Popen([
        sys.executable, "-m", "jupyter", "notebook",
        "--no-browser",
        "--NotebookApp.token=''",  # Notebook >=4.3
        "--port", str(port),
        "--log-level=DEBUG"], **kwargs)

    # wait for a few seconds to allow the notebook server to finish starting
    time.sleep(5)

    return server


def _close_nbserver(server):
    if sys.platform == 'win32':
        server.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        server.terminate()

    for _ in range(10):
        retcode = server.poll()
        if retcode is not None:
            break
        time.sleep(0.1)

    if retcode is None:
        print("couldn't shutdown notebook server, force killing it")
        server.kill()

    server.wait()
    copy_coverage_files()

    # wait a short period of time for kernels to finish shutting down
    time.sleep(1)


def _make_browser(tempdir):
    for filename in glob.glob(os.path.join(os.path.dirname(__file__), "files", "*.ipynb")):
        shutil.copy(filename, os.path.join(tempdir, os.path.basename(filename)))

    for filename in glob.glob(os.path.join(os.path.dirname(__file__), "files", "*.txt")):
        shutil.copy(filename, os.path.join(tempdir, os.path.basename(filename)))

    selenium_logger = logging.getLogger('selenium.webdriver.remote.remote_connection')
    selenium_logger.setLevel(logging.WARNING)

    capabilities = DesiredCapabilities.PHANTOMJS
    capabilities['loggingPrefs'] = {'browser': 'ALL'}
    browser = webdriver.PhantomJS(
        service_args=['--cookies-file=/dev/null', '--proxy-type=none'],
        desired_capabilities=capabilities,
        service_log_path=os.path.devnull)
    browser.set_page_load_timeout(30)
    browser.set_script_timeout(30)

    return browser


def _close_browser(browser):
    console_messages = browser.get_log('browser')
    if len(console_messages) > 0:
        print("\n<-- CAPTURED JAVASCRIPT CONSOLE MESSAGES -->")
        for message in console_messages:
            print(message)
        print("<------------------------------------------>")
    browser.save_screenshot(os.path.join(os.path.dirname(__file__), 'selenium.screenshot.png'))
    browser.service.process.send_signal(signal.SIGTERM)
    browser.quit()


notwindows = pytest.mark.skipif(
    sys.platform == 'win32',
    reason="Assignment List extension is not available on windows"
)
