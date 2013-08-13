#pylint: disable=C0111
#pylint: disable=W0621
from xmodule.util.mock_youtube_server.mock_youtube_server import MockYoutubeServer
from lettuce import before, after, world
from django.conf import settings
import threading

from logging import getLogger
logger = getLogger(__name__)


@before.all
def setup_mock_youtube_server():
    # import ipdb; ipdb.set_trace()
    server_host = '127.0.0.1'

    server_port = settings.VIDEO_PORT

    address = (server_host, server_port)

    # Create the mock server instance
    server = MockYoutubeServer(address)
    logger.debug("Youtube server started at {} port".format(str(server_port)))

    server.time_to_response = 0.1  # seconds

    server.address = address

    # Start the server running in a separate daemon thread
    # Because the thread is a daemon, it will terminate
    # when the main thread terminates.
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Store the server instance in lettuce's world
    # so that other steps can access it
    # (and we can shut it down later)
    world.youtube_server = server


@after.all
def teardown_mock_youtube_server(total):

    # Stop the LTI server and free up the port
    world.youtube_server.shutdown()
