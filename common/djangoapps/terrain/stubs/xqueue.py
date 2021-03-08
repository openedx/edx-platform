"""
Stub implementation of XQueue for acceptance tests.

Configuration values:
    "default" (dict): Default response to be sent to LMS as a grade for a submission
    "<submission>" (dict): Grade response to return for submissions containing the text <submission>
    "register_submission_url" (str): URL to send grader payloads when we receive a submission

If no grade response is configured, a default response will be returned.
"""


import copy
import json
from threading import Timer

from requests import post

from openedx.core.djangolib.markup import HTML

from .http import StubHttpRequestHandler, StubHttpService, require_params


class StubXQueueHandler(StubHttpRequestHandler):
    """
    A handler for XQueue POST requests.
    """

    DEFAULT_RESPONSE_DELAY = 2
    DEFAULT_GRADE_RESPONSE = {'correct': True, 'score': 1, 'msg': ''}

    @require_params('POST', 'xqueue_body', 'xqueue_header')
    def do_POST(self):
        """
        Handle a POST request from the client

        Sends back an immediate success/failure response.
        It then POSTS back to the client with grading results.
        """
        msg = f"XQueue received POST request {self.post_dict} to path {self.path}"
        self.log_message(msg)

        # Respond only to grading requests
        if self._is_grade_request():

            # If configured, send the grader payload to other services.
            # TODO TNL-3906
            # self._register_submission(self.post_dict['xqueue_body'])

            try:
                xqueue_header = json.loads(self.post_dict['xqueue_header'])
                callback_url = xqueue_header['lms_callback_url']

            except KeyError:
                # If the message doesn't have a header or body,
                # then it's malformed.  Respond with failure
                error_msg = "XQueue received invalid grade request"
                self._send_immediate_response(False, message=error_msg)

            except ValueError:
                # If we could not decode the body or header,
                # respond with failure
                error_msg = "XQueue could not decode grade request"
                self._send_immediate_response(False, message=error_msg)

            else:
                # Send an immediate response of success
                # The grade request is formed correctly
                self._send_immediate_response(True)

                # Wait a bit before POSTing back to the callback url with the
                # grade result configured by the server
                # Otherwise, the problem will not realize it's
                # queued and it will keep waiting for a response indefinitely
                delayed_grade_func = lambda: self._send_grade_response(
                    callback_url, xqueue_header, self.post_dict['xqueue_body']
                )

                delay = self.server.config.get('response_delay', self.DEFAULT_RESPONSE_DELAY)
                Timer(delay, delayed_grade_func).start()

        # If we get a request that's not to the grading submission
        # URL, return an error
        else:
            self._send_immediate_response(False, message="Invalid request URL")

    def _send_immediate_response(self, success, message=""):
        """
        Send an immediate success/failure message
        back to the client
        """

        # Send the response indicating success/failure
        response_str = json.dumps(
            {'return_code': 0 if success else 1, 'content': message}
        )

        if self._is_grade_request():
            self.send_response(
                200, content=response_str, headers={'Content-type': 'text/plain'}
            )
            self.log_message(f"XQueue: sent response {response_str}")

        else:
            self.send_response(500)

    def _send_grade_response(self, postback_url, xqueue_header, xqueue_body_json):
        """
        POST the grade response back to the client
        using the response provided by the server configuration.

        Uses the server configuration to determine what response to send:
        1) Specific response for submissions containing matching text in `xqueue_body`
        2) Default submission configured by client
        3) Default submission

        `postback_url` is the URL the client told us to post back to
        `xqueue_header` (dict) is the full header the client sent us, which we will send back
        to the client so it can authenticate us.
        `xqueue_body_json` (json-encoded string) is the body of the submission the client sent us.
        """
        # First check if we have a configured response that matches the submission body
        grade_response = None

        # This matches the pattern against the JSON-encoded xqueue_body
        # This is very simplistic, but sufficient to associate a student response
        # with a grading response.
        # There is a danger here that a submission will match multiple response patterns.
        # Rather than fail silently (which could cause unpredictable behavior in tests)
        # we abort and log a debugging message.
        for pattern, response in self.server.queue_responses:

            if pattern in xqueue_body_json:
                if grade_response is None:
                    grade_response = response

                # Multiple matches, so abort and log an error
                else:
                    self.log_error(
                        f"Multiple response patterns matched '{xqueue_body_json}'",
                    )
                    return

        # Fall back to the default grade response configured for this queue,
        # then to the default response.
        if grade_response is None:
            grade_response = self.server.config.get(
                'default', copy.deepcopy(self.DEFAULT_GRADE_RESPONSE)
            )

        # Wrap the message in <div> tags to ensure that it is valid XML
        if isinstance(grade_response, dict) and 'msg' in grade_response:
            grade_response['msg'] = HTML("<div>{0}</div>").format(grade_response['msg'])

        data = {
            'xqueue_header': json.dumps(xqueue_header),
            'xqueue_body': json.dumps(grade_response)
        }

        post(postback_url, data=data)
        self.log_message(f"XQueue: sent grading response {data} to {postback_url}")

    def _register_submission(self, xqueue_body_json):
        """
        If configured, send the submission's grader payload to another service.
        """
        url = self.server.config.get('register_submission_url')

        # If not configured, do not need to send anything
        if url is not None:

            try:
                xqueue_body = json.loads(xqueue_body_json)
            except ValueError:
                self.log_error(
                    f"Could not decode XQueue body as JSON: '{xqueue_body_json}'")

            else:

                # Retrieve the grader payload, which should be a JSON-encoded dict.
                # We pass the payload directly to the service we are notifying, without
                # inspecting the contents.
                grader_payload = xqueue_body.get('grader_payload')

                if grader_payload is not None:
                    response = post(url, data={'grader_payload': grader_payload})
                    if not response.ok:
                        self.log_error(
                            "Could register submission at URL '{}'.  Status was {}".format(
                                url, response.status_code))

                else:
                    self.log_message(
                        f"XQueue body is missing 'grader_payload' key: '{xqueue_body}'"
                    )

    def _is_grade_request(self):
        """
        Return a boolean indicating whether the requested URL indicates a submission.
        """
        return 'xqueue/submit' in self.path


class StubXQueueService(StubHttpService):
    """
    A stub XQueue grading server that responds to POST requests to localhost.
    """

    HANDLER_CLASS = StubXQueueHandler
    NON_QUEUE_CONFIG_KEYS = ['default', 'register_submission_url']

    @property
    def queue_responses(self):
        """
        Returns a list of (pattern, response) tuples, where `pattern` is a pattern
        to match in the XQueue body, and `response` is a dictionary to return
        as the response from the grader.

        Every configuration key is a queue name,
        except for 'default' and 'register_submission_url' which have special meaning
        """
        return list({
            key: value
            for key, value in self.config.items()
            if key not in self.NON_QUEUE_CONFIG_KEYS
        }.items())
