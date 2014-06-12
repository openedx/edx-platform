import os
import memcache
import subprocess
from invoke import task, Collection
from invoke.exceptions import Failure
try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text

from ..utils import chdir, singleton_process, wait_for_server
from ..utils.cmd import django_cmd
from ..utils.envs import Env

ns = Collection('bok_choy')

# Mongo databases that will be dropped before/after the tests run
BOK_CHOY_MONGO_DATABASE = 'test'

# Control parallel test execution with environment variables
# Process timeout is the maximum amount of time to wait for results from a particular test case
BOK_CHOY_NUM_PARALLEL = int(os.environ.get('NUM_PARALLEL', 1))
BOK_CHOY_TEST_TIMEOUT = float(os.environ.get('TEST_TIMEOUT', 300))

# Ensure that we have a directory to put logs and reports
BOK_CHOY_DIR = Env.REPO_ROOT/'common/test/acceptance'
BOK_CHOY_TEST_DIR = BOK_CHOY_DIR/'tests'
BOK_CHOY_LOG_DIR = Env.REPO_ROOT/'test_root/log'
BOK_CHOY_LOG_DIR.mkdir_p()

# Reports
BOK_CHOY_REPORT_DIR = Env.REPORT_DIR/'bok_choy'
BOK_CHOY_XUNIT_REPORT = BOK_CHOY_REPORT_DIR/'xunit.xml'
BOK_CHOY_COVERAGE_RC = BOK_CHOY_DIR/'.coveragerc'
BOK_CHOY_REPORT_DIR.mkdir_p()


# Directory that videos are served from
VIDEO_SOURCE_DIR = Env.REPO_ROOT/'test_root/data/video'

BOK_CHOY_SERVERS = {
    'lms': {
        'port':8003,
        'log': BOK_CHOY_LOG_DIR/'bok_choy_lms.log'
    },
    'cms': {
        'port': 8031,
        'log': BOK_CHOY_LOG_DIR/'bok_choy_studio.log'
    }
}

BOK_CHOY_STUBS = {

    'xqueue': {
        'port': 8040,
        'log': BOK_CHOY_LOG_DIR/'bok_choy_xqueue.log',
        'config': 'register_submission_url=http://0.0.0.0:8041/test/register_submission'
    },

    'ora': {
        'port': 8041,
        'log': BOK_CHOY_LOG_DIR/'bok_choy_ora.log',
        'config': ''
    },

    'comments': {
        'port': 4567,
        'log': BOK_CHOY_LOG_DIR/'bok_choy_comments.log'
    },

    'video': {
        'port': 8777,
        'log': BOK_CHOY_LOG_DIR/'bok_choy_video_sources.log',
        'config': "root_dir={video}".format(video=VIDEO_SOURCE_DIR)
    },

    'youtube': {
        'port': 9080,
        'log': BOK_CHOY_LOG_DIR/'bok_choy_youtube.log'
    }
}


# For the time being, stubs are used by both the bok-choy and lettuce acceptance tests
# For this reason, the stubs package is currently located in the Django app called "terrain"
# where other lettuce configuration is stored.
BOK_CHOY_STUB_DIR = Env.REPO_ROOT/'common/djangoapps/terrain'

BOK_CHOY_CACHE = memcache.Client(['localhost:11211'])


def start_servers():
    '''Start the servers we will run tests on'''

    for service, info in BOK_CHOY_SERVERS.items():
        address = "0.0.0.0:{}".format(innfo['port'])
        cmd = "coverage run --rcfile={rcfile} -m manage {service} --settings bok_choy runserver {address} --traceback --noreload".format(rcfile=BOK_CHOY_COVERAGE_RC,
                                                                                                                                          service=service,
                                                                                                                                          address=address)
        subprocess.Popen(cmd, shell=True, )

    for service, info in BOK_CHOY_STUBS:
        with chdir(BOK_CHOY_STUB_DIR):
            singleton_process(['python', '-m', 'stubs.start', service, info['port'], info['config'] ],
                              logfile=info['log'])

def wait_for_test_servers():
    '''Wait until we get a successful response from the servers or time out'''

    for service, info in BOK_CHOY_SERVERS + BOK_CHOY_STUBS:
        ready = wait_for_server("http://0.0.0.0", info['port'])
        if not ready:
            raise RuntimeError('Could not contact {service} test server'.format(service=service))

@task
def check_mongo():
    if not is_mongo_running():
        raise RuntimeError('Mongo is not running locally.')

@task
def check_mysql():
    if not is_mysql_running():
        raise RuntimeError('Mysql is not running locally')

@task
def check_memcache():
    if not is_memcach_running():
        raise RuntimeError('Memcache is not running locally')

@task('bok_choy.check_mongo',
      'bok_choy.check_memcache',
      'bok_choy.check_mysql'
)
def check_services():
    pass

@task('bok_choy.check_mysql',
      'prereqs.install'
)
def bok_choy_setup():
    sh(Env.REPO_ROOT/'scripts/reset-test-db.sh')
    sh("invoke assets.update --settings=bok_choy")

ns.add_task(bok_choy_setup, 'setup')

@task('bok_choy.check_services',
      'clean.reports')
def test_bok_choy_fast(spec=None):
    clear_mongo()
    BOK_CHOY_CACHE.flush()
    sh(django_cmd('lms', 'bok_choy', 'loaddata', 'common/test/db_fixtures/*.json'))

    # Ensure the test servers are available
    print(colorize('green', 'Starting test servers...'))
    start_servers()
    print(colorize('green', 'Waiting for servers to start...'))
    wait_for_test_servers()

    try:
        print(colorize('green', 'Running test suite...'))
        run_bok_choy(spec)
    except:
        print(colorize('red', 'Tests failed!'))
    finally:
        print(colorize('green', 'Cleaning up databases...'))

ns.add_task(test_bok_choy_fast, 'fast', default=True)

@task
def coverage():
    print(colorize('green', 'Combining coverage reports'))
    sh('coverage combine --rcfile={}'.format(BOK_CHOY_COVERAGE_RC))

    print(colorize('green', 'Generating coverage reports'))
    sh("coverage html --rcfile={}".format(BOK_CHOY_COVERAGE_RC))
    sh("coverage xml --rcfile={}".format(BOK_CHOY_COVERAGE_RC))
    sh("coverage report --rcfile={}".format(BOK_CHOY_COVERAGE_RC))

ns.add_task(coverage, 'coverage')


def is_mongo_running():
    '''
    The mongo command will connect to the service,
    failing with a non-zero exit code if it cannot connect.
    '''
    try:
        sh('''mongo --eval "print('running')"''' )
    except Failure:
        return False
    return True

def is_memcach_running():
    '''
    We use the memcache client to attempt to set a key
    in memcache.  If we cannot do so because the service is not
    available, then it will return 0.
    '''
    result = BOK_CHOY_CACHE.set('test', 'test')
    return result != 0

def is_mysql_running():
    '''
    We use the MySQL CLI client to list the available databases.
    If the mysql server is not up, the command will exit with a non-zero status
    '''
    try:
        sh('mysql -e "SHOW DATABASES"')
    except Failure:
        return False
    return True

def run_bok_choy(test_spec):
    '''
    '''

    # Default to running all tests if no test is specified
    if test_spec:
        test_spec = BOK_CHOY_TEST_DIR / test_spec
    else:
        test_spec = BOK_CHOY_TEST_DIR

    cmd = [
        "SCREENSHOT_DIR='{}'".format(BOK_CHOY_LOG_DIR), "nosetests", test_spec,
        "--with-xunit", "--with-flaky", "--xunit-file={}".format(BOK_CHOY_XUNIT_REPORT), "--verbosity=2"
    ]

    if BOK_CHOY_NUM_PARALLEL > 1:
        cmd += ["--processes={}".format(BOK_CHOY_NUM_PARALLEL), "--process-timeout={}".format(BOK_CHOY_TEST_TIMEOUT)]

    sh(' '.join(cmd))

def cleanup():
    sh(django_cmd('lms', 'bok_choy', 'flush', '--no-input'))
    clear_mongo()

def clear_mongo():
    sh("mongo {} --eval 'db.dropDatabase()'".format(BOK_CHOY_MONGO_DATABASE))
