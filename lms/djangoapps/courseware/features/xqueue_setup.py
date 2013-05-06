#pylint: disable=C0111
#pylint: disable=W0621

from courseware.mock_xqueue_server.mock_xqueue_server import MockXQueueServer
from lettuce import before, after, world
from django.conf import settings
import threading

@before.all
def setup_mock_xqueue_server():

    # Retrieve the local port from settings
    server_port = settings.XQUEUE_PORT

    # Create the mock server instance
    server = MockXQueueServer(server_port)

    # Start the server running in a separate daemon thread
    # Because the thread is a daemon, it will terminate
    # when the main thread terminates.
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Store the server instance in lettuce's world
    # so that other steps can access it
    # (and we can shut it down later)
    world.xqueue_server = server


@after.all
def teardown_mock_xqueue_server(total):

    # Stop the xqueue server and free up the port
    world.xqueue_server.shutdown()
