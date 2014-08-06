"""
Helper functions for bok_choy test tasks
"""
import sys
import os
import time
import httplib
import subprocess
from paver.easy import sh
from pavelib.utils.envs import Env
from pavelib.utils.process import run_background_process

try:
    from pygments.console import colorize
except ImportError:
    colorize = lambda color, text: text  # pylint: disable-msg=invalid-name

__test__ = False  # do not collect


def start_servers():
    """
    Start the servers we will run tests on, returns PIDs for servers.
    """

    def start_server(cmd, logfile, cwd=None):
        """
        Starts a single server.
        """
        print cmd, logfile
        run_background_process(cmd, out_log=logfile, err_log=logfile, cwd=cwd)

    for service, info in Env.BOK_CHOY_SERVERS.iteritems():
        address = "0.0.0.0:{}".format(info['port'])
        cmd = (
            "coverage run --rcfile={coveragerc} -m "
            "manage {service} --settings bok_choy runserver "
            "{address} --traceback --noreload".format(
                coveragerc=Env.BOK_CHOY_COVERAGERC,
                service=service,
                address=address,
            )
        )
        start_server(cmd, info['log'])

    for service, info in Env.BOK_CHOY_STUBS.iteritems():
        cmd = (
            "python -m stubs.start {service} {port} "
            "{config}".format(
                service=service,
                port=info['port'],
                config=info.get('config', ''),
            )
        )
        start_server(cmd, info['log'], cwd=Env.BOK_CHOY_STUB_DIR)


def wait_for_server(server, port):
    """
    Wait for a server to respond with status 200
    """
    print(
        "Checking server {server} on port {port}".format(
            server=server,
            port=port,
        )
    )

    attempts = 0
    server_ok = False

    while attempts < 20:
        try:
            connection = httplib.HTTPConnection(server, port, timeout=10)
            connection.request('GET', '/')
            response = connection.getresponse()

            if int(response.status) == 200:
                server_ok = True
                break
        except:  # pylint: disable-msg=bare-except
            pass

        attempts += 1
        time.sleep(1)

    return server_ok


def wait_for_test_servers():
    """
    Wait until we get a successful response from the servers or time out
    """

    for service, info in Env.BOK_CHOY_SERVERS.iteritems():
        ready = wait_for_server("0.0.0.0", info['port'])
        if not ready:
            msg = colorize(
                "red",
                "Could not contact {} test server".format(service)
            )
            print(msg)
            sys.exit(1)


def is_mongo_running():
    """
    Returns True if mongo is running, False otherwise.
    """
    # The mongo command will connect to the service,
    # failing with a non-zero exit code if it cannot connect.
    output = os.popen('mongo --eval "print(\'running\')"').read()
    return (output and "running" in output)


def is_memcache_running():
    """
    Returns True if memcache is running, False otherwise.
    """
    # Attempt to set a key in memcache. If we cannot do so because the
    # service is not available, then this will return False.
    return Env.BOK_CHOY_CACHE.set('test', 'test')


def is_mysql_running():
    """
    Returns True if mysql is running, False otherwise.
    """
    # We need to check whether or not mysql is running as a process
    # even if it is not daemonized.
    with open(os.devnull, 'w') as DEVNULL:
        #pgrep returns the PID, which we send to /dev/null
        returncode = subprocess.call("pgrep mysqld", stdout=DEVNULL, shell=True)
    return returncode == 0


def clear_mongo():
    """
    Clears mongo database.
    """
    sh(
        "mongo {} --eval 'db.dropDatabase()' > /dev/null".format(
            Env.BOK_CHOY_MONGO_DATABASE,
        )
    )


def check_mongo():
    """
    Check that mongo is running
    """
    if not is_mongo_running():
        msg = colorize('red', "Mongo is not running locally.")
        print(msg)
        sys.exit(1)


def check_memcache():
    """
    Check that memcache is running
    """
    if not is_memcache_running():
        msg = colorize('red', "Memcache is not running locally.")
        print(msg)
        sys.exit(1)


def check_mysql():
    """
    Check that mysql is running
    """
    if not is_mysql_running():
        msg = colorize('red', "MySQL is not running locally.")
        print(msg)
        sys.exit(1)


def check_services():
    """
    Check that all required services are running
    """
    check_mongo()
    check_memcache()
    check_mysql()
