#pylint: disable=C0111
#pylint: disable=W0621

from courseware.mock_lti_server.mock_lti_server import MockLTIServer
from lettuce import before, after, world
from django.conf import settings
import threading

from logging import getLogger
logger = getLogger(__name__)


@before.all
def setup_mock_lti_server():

    server_host = '127.0.0.1'
    server_port = settings.LTI_PORT

    address = (server_host, server_port)

    # Create the mock server instance
    server = MockLTIServer(address)
    logger.debug("LTI server started at {} port".format(str(server_port)))
    # Start the server running in a separate daemon thread
    # Because the thread is a daemon, it will terminate
    # when the main thread terminates.
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    server.server_host = server_host
    server.oauth_settings = {
        'client_key': 'test_client_key',
        'client_secret': 'test_client_secret',
        'lti_base':  'http://{}:{}/'.format(server_host, server_port),
        'lti_endpoint': 'correct_lti_endpoint'
    }

    # Store the server instance in lettuce's world
    # so that other steps can access it
    # (and we can shut it down later)
    world.lti_server = server


@after.all
def teardown_mock_lti_server(total):

    # Stop the LTI server and free up the port
    world.lti_server.shutdown()
