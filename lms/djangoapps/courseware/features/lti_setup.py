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

    # Add +1 to XQUEUE random port number
    server_port = settings.XQUEUE_PORT + 1

    # Create the mock server instance
    server = MockLTIServer(server_port)
    logger.debug("LTI server started at {} port".format(str(server_port)))
    # Start the server running in a separate daemon thread
    # Because the thread is a daemon, it will terminate
    # when the main thread terminates.
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Store the server instance in lettuce's world
    # so that other steps can access it
    # (and we can shut it down later)
    world.lti_server = server
    world.lti_server_port = server_port


@after.all
def teardown_mock_lti_server(total):

    # Stop the LTI server and free up the port
    world.lti_server.shutdown()
