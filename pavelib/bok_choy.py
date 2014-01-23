# Run acceptance tests that use the bok-choy framework
# http://bok-choy.readthedocs.org/en/latest/

from paver.easy import *
from pavelib import prereqs, proc_utils, paver_utils, assets, django
import memcache
import os


# Mongo databases that will be dropped before/after the tests run
BOK_CHOY_MONGO_DB = "test"

# Control parallel test execution with environment variables
# Process timeout is the maximum amount of time to wait for results from a particular test case
BOK_CHOY_NUM_PARALLEL = os.getenv('NUM_PARALLEL', 1)
BOK_CHOY_TEST_TIMEOUT = os.getenv('TEST_TIMEOUT', 300)

# Ensure that we have a directory to put logs and reports
BOK_CHOY_TEST_DIR = os.path.join(assets.REPO_ROOT, "common", "test", "acceptance", "tests")
BOK_CHOY_LOG_DIR = os.path.join(assets.REPO_ROOT, "test_root", "log")

BOK_CHOY_SERVERS = [{'system': 'lms', 'port': 8003, 'log': os.path.join(BOK_CHOY_LOG_DIR, 'bok_choy_lms.log')},
                    {'system': 'cms', 'port': 8031, 'log': os.path.join(BOK_CHOY_LOG_DIR, 'bok_choy_studio.log')},
                    ]

BOK_CHOY_CACHE = None


# Start the server we will run tests on
def start_servers():
    for server in BOK_CHOY_SERVERS:
        system = server['system']
        port = server['port']
        address = "0.0.0.0:{port}".format(port=port)
        log = server['log']

        pids = proc_utils.run_process([
            'python manage.py {system} runserver --traceback --settings=bok_choy {address}'.format(
            system=system, address=address)], False, log)

        server['running_pid'] = pids[0]


# Wait until we get a successful response from the servers or time out
def wait_for_test_servers():
    for server in BOK_CHOY_SERVERS:
        port = server['port']
        address = "http://127.0.0.1:{port}".format(port=port)
        ready = proc_utils.wait_for_server(address)
        if not ready:
            raise Exception(
                paver_utils.colorize_red("Could not contact {server} test server".format(
                    server=server['system'])))


def is_mongo_running():
    # The mongo command will connect to the service,
    # failing with a non-zero exit code if it cannot connect.
    output = sh("mongo --eval \"print('running')\"", capture=True)
    if not "running" in output:
        return False

    return True


def is_memcache_running():
    global BOK_CHOY_CACHE
    try:
        BOK_CHOY_CACHE = memcache.Client(['127.0.0.1:11211'])
        BOK_CHOY_CACHE.set('test', 'test')
        return True
    except Exception as e:
        print(e.message)
        return False


def is_mysql_running():
    # We use the MySQL CLI client and capture its stderr
    # If the client cannot connect successfully, stderr will be non-empty
    output = sh("mysql -e ' ' ", capture=True)
    if not output:
        return True
    else:
        return False


def nose_cmd(test_spec):
    cmd = ["SCREENSHOT_DIR='{BOK_CHOY_LOG_DIR}'".format(BOK_CHOY_LOG_DIR=BOK_CHOY_LOG_DIR), "nosetests", test_spec]
    if BOK_CHOY_NUM_PARALLEL > 1:
        cmd += ["--processes={BOK_CHOY_NUM_PARALLEL}".format(BOK_CHOY_NUM_PARALLEL=BOK_CHOY_NUM_PARALLEL),
                "--process-timeout={BOK_CHOY_TEST_TIMEOUT}".format(BOK_CHOY_TEST_TIMEOUT=BOK_CHOY_TEST_TIMEOUT)]

    return ' '.join(cmd)


# Run the bok choy tests
# `test_spec` is a nose-style test specifier relative to the test directory
# Examples:
# - path/to/test.py
# - path/to/test.py:TestFoo
# - path/to/test.py:TestFoo.test_bar
# It can also be left blank to run all tests in the suite.
def run_bok_choy(test_spec):
    if not test_spec:
        print(nose_cmd(BOK_CHOY_TEST_DIR))
        sh(nose_cmd(BOK_CHOY_TEST_DIR))
    else:
        sh(nose_cmd(os.path.join(BOK_CHOY_TEST_DIR, test_spec)))


def clear_mongo():
    sh("mongo {BOK_CHOY_MONGO_DB} --eval 'db.dropDatabase()' > /dev/null".format(BOK_CHOY_MONGO_DB=BOK_CHOY_MONGO_DB))


# Clean up data we created in the databases
def cleanup():
    sh('python manage.py lms --settings=bok_choy flush --noinput')
    clear_mongo()
    # stop servers if running
    for server in BOK_CHOY_SERVERS:
        if 'running_pid' in server:
            proc_utils.kill_process(server['running_pid'])


def check_running():

    # Check that required services are running
    if not is_mongo_running():
        raise Exception(paver_utils.print_red("Mongo is not running locally."))

    if not is_memcache_running():
        raise Exception(paver_utils.print_red("Memcache is not running locally."))

    if not is_mysql_running():
        raise Exception(paver_utils.print_red("MySQL is not running locally."))


@task
@cmdopts([
    ("system=", "s", "System to act on"),
])
def bok_choy_setup(options):
    """
    Process assets and set up database for bok-choy tests"
    """

    check_running()
    prereqs.install_prereqs()

    # Clear any test data already in Mongo
    clear_mongo()

    # Invalidate the cache
    BOK_CHOY_CACHE.flush_all()

    # HACK: Since the CMS depends on the existence of some database tables
    # that are now in common but used to be in LMS (Role/Permissions for Forums)
    # we need to create/migrate the database tables defined in the LMS.
    # We might be able to address this by moving out the migrations from
    # lms/django_comment_client, but then we'd have to repair all the existing
    # migrations from the upgrade tables in the DB.
    # But for now for either system (lms or cms), use the lms
    # definitions to sync and migrate.

    setattr(options, 'system', 'lms')
    setattr(options, 'env', 'bok_choy')
    django.resetdb(options)

    setattr(options, 'action', 'syncdb')
    django.django_admin(options)

    setattr(options, 'action', 'migrate')
    django.django_admin(options)

    assets.compile_assets(options)
    setattr(options, 'system', 'cms')
    assets.compile_assets(options)


@task
@cmdopts([
    ("test_spec=", "t", "Test specification"),
])
def test_bok_choy_fast(options):
    """
    Run acceptance tests that use the bok-choy framework but skip setup
    """

    test_spec = getattr(options, 'test_spec', '')

    # Ensure the test servers are available
    paver_utils.print_red("Starting test servers...")
    start_servers()
    paver_utils.print_red("Waiting for servers to start...")
    wait_for_test_servers()
    paver_utils.print_red("Servers started")
    paver_utils.print_red("Running test suite...")
    try:
        run_bok_choy(test_spec)
    except Exception as e:
        paver_utils.print_red('Tests failed because: {exception}'.format(exception=e.message))
        exit(1)
    finally:
        paver_utils.print_red("Cleaning up databases...")
        cleanup()


@task
@cmdopts([
    ("test_spec=", "t", "Test specification"),
])
def test_bok_choy(options):
    """
    Run acceptance tests that use the bok-choy framework
    """
    bok_choy_setup(options)
    test_bok_choy_fast(options)
