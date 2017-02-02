"""
Serve HTML5 video sources for acceptance tests
"""
from SimpleHTTPServer import SimpleHTTPRequestHandler
from .http import StubHttpService
from contextlib import contextmanager
import os

from logging import getLogger
LOGGER = getLogger(__name__)


class VideoSourceRequestHandler(SimpleHTTPRequestHandler):
    """
    Request handler for serving video sources locally.
    """
    def translate_path(self, path):
        """
        Remove any extra parameters from the path.
        For example /gizmo.mp4?1397160769634
        becomes /gizmo.mp4
        """
        root_dir = self.server.config.get('root_dir')
        path = '{}{}'.format(root_dir, path)
        return path.split('?')[0]


class VideoSourceHttpService(StubHttpService):
    """
    Simple HTTP server for serving HTML5 Video sources locally for tests
    """
    HANDLER_CLASS = VideoSourceRequestHandler

    def __init__(self, port_num=0):

        @contextmanager
        def _remember_cwd():
            """
            Files are automatically served from the current directory
            so we need to change it, start the server, then set it back.
            """
            curdir = os.getcwd()
            try:
                yield
            finally:
                os.chdir(curdir)

        with _remember_cwd():
            StubHttpService.__init__(self, port_num=port_num)
