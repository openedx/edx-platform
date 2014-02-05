"""
LTI Server

What is supported:
------------------

1.) This LTI Provider can service only one Tool Consumer at the same time. It is
not possible to have this LTI multiple times on a single page in LMS.

"""
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from uuid import uuid4
import textwrap
import urlparse
from oauthlib.oauth1.rfc5849 import signature
import oauthlib.oauth1
import hashlib
import base64
import mock
import sys
import requests
import textwrap

from logging import getLogger
logger = getLogger(__name__)


class MockLTIRequestHandler(BaseHTTPRequestHandler):
    '''
    A handler for LTI POST requests.
    '''

    protocol = "HTTP/1.0"
    callback_url = None

    def log_message(self, format, *args):
        """Log an arbitrary message."""
        # Code copied from BaseHTTPServer.py. Changed to write to sys.stdout
        # so that messages won't pollute test output.
        sys.stdout.write("%s - - [%s] %s\n" %
                         (self.client_address[0],
                          self.log_date_time_string(),
                          format % args))

    def do_GET(self):
        '''
        Handle a GET request from the client and sends response back.

        Used for checking LTI Provider started correctly.
        '''
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'html')
        self.end_headers()
        response_str = """<html><head><title>TEST TITLE</title></head>
            <body>This is LTI Provider.</body></html>"""
        self.wfile.write(response_str)

    def do_POST(self):
        '''
        Handle a POST request from the client and sends response back.
        '''
        if 'grade' in self.path and self._send_graded_result().status_code == 200:
            status_message = 'LTI consumer (edX) responded with XML content:<br>' + self.server.grade_data['TC answer']
            self.server.grade_data = None
            self._send_response(status_message, 200)
        # Respond to request with correct lti endpoint:
        elif self._is_correct_lti_request():
            self.post_dict = self._post_dict()
            params = {k: v for k, v in self.post_dict.items() if k != 'oauth_signature'}
            if self.server.check_oauth_signature(params, self.post_dict.get('oauth_signature', "")):
                status_message = "This is LTI tool. Success."
                # set data for grades what need to be stored as server data
                if 'lis_outcome_service_url' in self.post_dict:
                    self.server.grade_data = {
                        'callback_url': self.post_dict.get('lis_outcome_service_url'),
                        'sourcedId': self.post_dict.get('lis_result_sourcedid')
                    }
            else:
                status_message = "Wrong LTI signature"
            self._send_response(status_message, 200)
        else:
            status_message = "Invalid request URL"
            self._send_response(status_message, 500)

    def _send_head(self, status_code):
        '''
        Send the response code and MIME headers
        '''
        self.send_response(status_code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _post_dict(self):
        '''
        Retrieve the POST parameters from the client as a dictionary
        '''
        try:
            length = int(self.headers.getheader('content-length'))
            post_dict = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=True)
            # The POST dict will contain a list of values for each key.
            # None of our parameters are lists, however, so we map [val] --> val.
            # If the list contains multiple entries, we pick the first one
            post_dict = {key: val[0] for key, val in post_dict.items()}
        except:
            # We return an empty dict here, on the assumption
            # that when we later check that the request has
            # the correct fields, it won't find them,
            # and will therefore send an error response
            return {}
        try:
            cookie = self.headers.getheader('cookie')
            self.server.cookie = {k.strip(): v[0] for k, v in urlparse.parse_qs(cookie).items()}
        except:
            self.server.cookie = {}
        referer = urlparse.urlparse(self.headers.getheader('referer'))
        self.server.referer_host = "{}://{}".format(referer.scheme, referer.netloc)
        return post_dict

    def _send_graded_result(self):
        """
        Send grade request.
        """
        values = {
            'textString': 0.5,
            'sourcedId': self.server.grade_data['sourcedId'],
            'imsx_messageIdentifier': uuid4().hex,
        }
        payload = textwrap.dedent("""
            <?xml version = "1.0" encoding = "UTF-8"?>
                <imsx_POXEnvelopeRequest  xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
                  <imsx_POXHeader>
                    <imsx_POXRequestHeaderInfo>
                      <imsx_version>V1.0</imsx_version>
                      <imsx_messageIdentifier>{imsx_messageIdentifier}</imsx_messageIdentifier> /
                    </imsx_POXRequestHeaderInfo>
                  </imsx_POXHeader>
                  <imsx_POXBody>
                    <replaceResultRequest>
                      <resultRecord>
                        <sourcedGUID>
                          <sourcedId>{sourcedId}</sourcedId>
                        </sourcedGUID>
                        <result>
                          <resultScore>
                            <language>en-us</language>
                            <textString>{textString}</textString>
                          </resultScore>
                        </result>
                      </resultRecord>
                    </replaceResultRequest>
                  </imsx_POXBody>
                </imsx_POXEnvelopeRequest>
        """)
        data = payload.format(**values)
        if getattr(self.server, 'use_real_callback_url', None):
            # Use exact URL that was sent from TC when using this Stub LTI server
            # as TP in real standalone environment.
            url = self.server.grade_data['callback_url']
        else:
            # Use relative URL when using TP locally for manual testing or jenkins.
            relative_url = urlparse.urlparse(self.server.grade_data['callback_url']).path
            url = self.server.referer_host + relative_url

        headers = {'Content-Type': 'application/xml', 'X-Requested-With': 'XMLHttpRequest'}
        headers['Authorization'] = self.oauth_sign(url, data)

        # We can't mock requests in unit tests, because we use them, but we need
        # them to be mocked only for this one case.
        if getattr(self.server, 'run_inside_unittest_flag', None):
            response = mock.Mock(status_code=200, url=url, data=data, headers=headers)
            return response
        # Send request ignoring verification of SSL certificate
        response = requests.post(
            url,
            data=data,
            headers=headers,
            verify=False
        )
        self.server.grade_data['TC answer'] = response.content
        return response

    def _send_response(self, message, status_code):
        '''
        Send message back to the client
        '''
        self._send_head(status_code)
        if getattr(self.server, 'grade_data', False):  # lti can be graded
            url = "//%s:%s" % self.server.server_address
            response_str = textwrap.dedent("""
                <html>
                    <head>
                        <title>TEST TITLE</title>
                    </head>
                    <body>
                        <div>
                            <h2>Graded IFrame loaded</h2>
                            <h3>Server response is:</h3>
                            <h3 class="result">{}</h3>
                            <h5>Role: {role}</h5>
                        </div>
                        <form action="{url}/grade" method="post">
                            <input type="submit" name="submit-button" value="Submit">
                        </form>
                    </body>
                </html>
            """).format(message, role=self.post_dict['roles'], url=url)
        else: # lti can't be graded
            response_str = textwrap.dedent("""
                <html>
                    <head>
                        <title>TEST TITLE</title>
                    </head>
                    <body>
                        <div>
                            <h2>IFrame loaded</h2>
                            <h3>Server response is:</h3>
                            <h3 class="result">{}</h3>

                        </div>
                    </body>
                </html>
            """).format(message)

        logger.debug("LTI: sent response {}".format(response_str))
        self.wfile.write(response_str)

    def _is_correct_lti_request(self):
        '''
        If url to LTI tool is correct.
        '''
        return self.server.oauth_settings['lti_endpoint'] in self.path

    def oauth_sign(self, url, body):
        """
        Signs request and returns signed body and headers.
        """
        client = oauthlib.oauth1.Client(
            client_key=unicode(self.server.oauth_settings['client_key']),
            client_secret=unicode(self.server.oauth_settings['client_secret'])
        )
        headers = {
            # This is needed for body encoding:
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        #Calculate and encode body hash. See http://oauth.googlecode.com/svn/spec/ext/body_hash/1.0/oauth-bodyhash.html
        sha1 = hashlib.sha1()
        sha1.update(body)
        oauth_body_hash = base64.b64encode(sha1.digest())
        __, headers, __ = client.sign(
            unicode(url.strip()),
            http_method=u'POST',
            body={u'oauth_body_hash': oauth_body_hash},
            headers=headers
        )
        headers = headers['Authorization'] + ', oauth_body_hash="{}"'.format(oauth_body_hash)
        return headers


class MockLTIServer(HTTPServer):
    '''
    A mock LTI provider server that responds
    to POST requests to localhost.
    '''

    def __init__(self, address):
        '''
        Initialize the mock XQueue server instance.

        *address* is the (host, host's port to listen to) tuple.
        '''
        handler = MockLTIRequestHandler
        HTTPServer.__init__(self, address, handler)

    def shutdown(self):
        '''
        Stop the server and free up the port
        '''
        # First call superclass shutdown()
        HTTPServer.shutdown(self)
        # We also need to manually close the socket
        self.socket.close()

    def check_oauth_signature(self, params, client_signature):
        '''
        Checks oauth signature from client.

        `params` are params from post request except signature,
        `client_signature` is signature from request.

        Builds mocked request and verifies hmac-sha1 signing::
            1. builds string to sign from `params`, `url` and `http_method`.
            2. signs it with `client_secret` which comes from server settings.
            3. obtains signature after sign and then compares it with request.signature
            (request signature comes form client in request)

        Returns `True` if signatures are correct, otherwise `False`.

        '''
        client_secret = unicode(self.oauth_settings['client_secret'])
        url = self.oauth_settings['lti_base'] + self.oauth_settings['lti_endpoint']

        request = mock.Mock()

        request.params = [(unicode(k), unicode(v)) for k, v in params.items()]
        request.uri = unicode(url)
        request.http_method = u'POST'
        request.signature = unicode(client_signature)
        return signature.verify_hmac_sha1(request, client_secret)

