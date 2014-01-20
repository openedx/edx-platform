"""
Stub implementation of an HTTP service.
"""

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import urlparse
import threading
import json
from lazy import lazy

from logging import getLogger
LOGGER = getLogger(__name__)


class StubHttpRequestHandler(BaseHTTPRequestHandler, object):
    """
    Handler for the stub HTTP service.
    """

    protocol = "HTTP/1.0"

    def log_message(self, format_str, *args):
        """
        Redirect messages to keep the test console clean.
        """

        msg = "{0} - - [{1}] {2}\n".format(
            self.client_address[0],
            self.log_date_time_string(),
            format_str % args
        )

        LOGGER.debug(msg)

    @lazy
    def request_content(self):
        """
        Retrieve the content of the request.
        """
        try:
            length = int(self.headers.getheader('content-length'))

        except (TypeError, ValueError):
            return ""
        else:
            return self.rfile.read(length)

    @lazy
    def post_dict(self):
        """
        Retrieve the request POST parameters from the client as a dictionary.
        If no POST parameters can be interpreted, return an empty dict.
        """
        contents = self.request_content

        # The POST dict will contain a list of values for each key.
        # None of our parameters are lists, however, so we map [val] --> val
        # If the list contains multiple entries, we pick the first one
        try:
            post_dict = urlparse.parse_qs(contents, keep_blank_values=True)
            return {
                key: list_val[0]
                for key, list_val in post_dict.items()
            }

        except:
            return dict()

    @lazy
    def get_params(self):
        """
        Return the GET parameters (querystring in the URL).
        """
        return urlparse.parse_qs(self.path)

    def do_PUT(self):
        """
        Allow callers to configure the stub server using the /set_config URL.
        """
        if self.path == "/set_config" or self.path == "/set_config/":

            for key, value in self.post_dict.iteritems():
                self.log_message("Set config '{0}' to '{1}'".format(key, value))

                try:
                    value = json.loads(value)

                except ValueError:
                    self.log_message(u"Could not parse JSON: {0}".format(value))
                    self.send_response(400)

                else:
                    self.server.set_config(unicode(key, 'utf-8'), value)
                    self.send_response(200)

        else:
            self.send_response(404)

    def send_response(self, status_code, content=None, headers=None):
        """
        Send a response back to the client with the HTTP `status_code` (int),
        `content` (str) and `headers` (dict).
        """
        self.log_message(
            "Sent HTTP response: {0} with content '{1}' and headers {2}".format(status_code, content, headers)
        )

        if headers is None:
            headers = dict()

        BaseHTTPRequestHandler.send_response(self, status_code)

        for (key, value) in headers.items():
            self.send_header(key, value)

        if len(headers) > 0:
            self.end_headers()

        if content is not None:
            self.wfile.write(content)


class StubHttpService(HTTPServer, object):
    """
    Stub HTTP service implementation.
    """

    # Subclasses override this to provide the handler class to use.
    # Should be a subclass of `StubHttpRequestHandler`
    HANDLER_CLASS = StubHttpRequestHandler

    def __init__(self, port_num=0):
        """
        Configure the server to listen on localhost.
        Default is to choose an arbitrary open port.
        """
        address = ('127.0.0.1', port_num)
        HTTPServer.__init__(self, address, self.HANDLER_CLASS)

        # Create a dict to store configuration values set by the client
        self._config = dict()

        # Start the server in a separate thread
        server_thread = threading.Thread(target=self.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        # Log the port we're using to help identify port conflict errors
        LOGGER.debug('Starting service on port {0}'.format(self.port))

    def shutdown(self):
        """
        Stop the server and free up the port
        """
        # First call superclass shutdown()
        HTTPServer.shutdown(self)

        # We also need to manually close the socket
        self.socket.close()

    @property
    def port(self):
        """
        Return the port that the service is listening on.
        """
        _, port = self.server_address
        return port

    def config(self, key, default=None):
        """
        Return the configuration value for `key`.  If this
        value has not been set, return `default` instead.
        """
        return self._config.get(key, default)

    def set_config(self, key, value):
        """
        Set the configuration `value` for `key`.
        """
        self._config[key] = value

