"""
Upload HTML files to tenon.io for accessibility scoring.
"""
import logging
import requests

log = logging.getLogger(__name__)


class AccessibilityTest:
    """
    A class for sending HTML source to the tenon.io API and determining any accessibility issues.

    Attributes:
        key (str): your tenon.io API key
        src (str): HTML source to rate
        url (str): URL of tenon API, defaults to 'https://tenon.io/api/'
    """
    def __init__(self, src, key, url='https://tenon.io/api/'):
        self.url = url
        self.key = key
        self.src = src

    @property
    def test_response(self):
        """
        Send the request to tenon.io for the given html source.

        Returns:
            TenonResponse object

        Raises:
            error for 4XX or 5XX response or any other Exception
        """
        try:
            data = {'key': self.key, 'src': self.src}
            resp = requests.post(self.url, data=data)

            # Raise exception if 4XX or 5XX response code is returned
            resp.raise_for_status()

        except Exception as e:
            log.error(e.message)
            raise

        return TenonResponse(resp)


class TenonResponse(object):
    """
    A class for parsing the tenon.io API response

    Attributes:
        response: The request response object
    """
    def __init__(self, response):
        self.response = response
        self.json = response.json()

    @property
    def api_errors(self):
        return self.json.get('apiErrors')

    @property
    def document_size(self):
        return self.json.get('documentSize')

    @property
    def global_stats(self):
        return self.json.get('globalStats')

    @property
    def message(self):
        return self.json.get('message')

    @property
    def request(self):
        return self.json.get('request')

    @property
    def response_exec_time(self):
        return self.json.get('responseExecTime')

    @property
    def response_time(self):
        return self.json.get('responseTime')

    @property
    def result_set(self):
        return self.json.get('resultSet')

    @property
    def result_summary(self):
        return self.json.get('resultSummary')

    @property
    def source_hash(self):
        return self.json.get('sourceHash')

    @property
    def client_script_errors(self):
        return self.json.get('clientScriptErrors')


class TenonIssue(object):
    """
    Issue reported via tenon.io test results

    Attributes:
        issue (string): A single issue from the result_set node
        of the tenon response
    """
    def __init__(self, issue):
        self.issue = issue

    @property
    def bp_id(self):
        return self.issue.get('bpID')

    @property
    def certainty(self):
        return self.issue.get('certainty')

    @property
    def priority(self):
        return self.issue.get('priority')

    @property
    def error_description(self):
        return self.issue.get('errorDescription')

    @property
    def error_snippet(self):
        return self.issue.get('errorSnippet')

    @property
    def error_title(self):
        return self.issue.get('errorTitle')

    @property
    def result_title(self):
        return self.issue.get('resultTitle')

    @property
    def standards(self):
        return self.issue.get('standards')

    @property
    def t_id(self):
        return self.issue.get('tID')

    @property
    def xpath(self):
        return self.issue.get('xpath')
