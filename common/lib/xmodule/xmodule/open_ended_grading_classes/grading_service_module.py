# This class gives a common interface for logging into the grading controller

import logging

import requests
import dogstats_wrapper as dog_stats_api
from lxml import etree
from requests.exceptions import RequestException, ConnectionError, HTTPError

from .combined_open_ended_rubric import CombinedOpenEndedRubric, RubricParsingError

log = logging.getLogger(__name__)


class GradingServiceError(Exception):
    """
    Exception for grading service.  Shown when Open Response Assessment servers cannot be reached.
    """
    pass


class GradingService(object):
    """
    Interface to staff grading backend.
    """

    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.session = requests.Session()
        self.render_template = config['render_template']

    def _login(self):
        """
        Log into the staff grading service.

        Raises requests.exceptions.HTTPError if something goes wrong.

        Returns the decoded json dict of the response.
        """
        response = self.session.post(self.login_url,
                                     {'username': self.username,
                                      'password': self.password, })

        response.raise_for_status()

        return response.json()

    def _metric_name(self, suffix):
        """
        Return a metric name for datadog, using `self.METRIC_NAME` as
        a prefix, and `suffix` as the suffix.

        Arguments:
            suffix (str): The metric suffix to use.
        """
        return '{}.{}'.format(self.METRIC_NAME, suffix)

    def _record_result(self, action, data, tags=None):
        """
        Log results from an API call to an ORA service to datadog.

        Arguments:
            action (str): The ORA action being recorded.
            data (dict): The data returned from the ORA service. Should contain the key 'success'.
            tags (list): A list of tags to attach to the logged metric.
        """
        if tags is None:
            tags = []

        tags.append(u'result:{}'.format(data.get('success', False)))
        tags.append(u'action:{}'.format(action))
        dog_stats_api.increment(self._metric_name('request.count'), tags=tags)

    def post(self, url, data, allow_redirects=False):
        """
        Make a post request to the grading controller. Returns the parsed json results of that request.
        """
        try:
            op = lambda: self.session.post(url, data=data,
                                           allow_redirects=allow_redirects)
            response_json = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError, ValueError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            #This is a dev_facing_error
            error_string = "Problem posting data to the grading controller.  URL: {0}, data: {1}".format(url, data)
            log.error(error_string)
            raise GradingServiceError(error_string)

        return response_json

    def get(self, url, params, allow_redirects=False):
        """
        Make a get request to the grading controller. Returns the parsed json results of that request.
        """
        op = lambda: self.session.get(url,
                                      allow_redirects=allow_redirects,
                                      params=params)
        try:
            response_json = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError, ValueError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            #This is a dev_facing_error
            error_string = "Problem getting data from the grading controller.  URL: {0}, params: {1}".format(url, params)
            log.error(error_string)
            raise GradingServiceError(error_string)

        return response_json

    def _try_with_login(self, operation):
        """
        Call operation(), which should return a requests response object.  If
        the request fails with a 'login_required' error, call _login() and try
        the operation again.

        Returns the result of operation().  Does not catch exceptions.
        """
        response = operation()
        resp_json = response.json()
        if (resp_json
                and resp_json.get('success') is False
                and resp_json.get('error') == 'login_required'):
            # apparently we aren't logged in.  Try to fix that.
            r = self._login()
            if r and not r.get('success'):
                log.warning("Couldn't log into ORA backend. Response: %s",
                            r)
            # try again
            response = operation()
            response.raise_for_status()
            resp_json = response.json()

        return resp_json

    def _render_rubric(self, response, view_only=False):
        """
        Given an HTTP Response json with the key 'rubric', render out the html
        required to display the rubric and put it back into the response

        returns the updated response as a dictionary that can be serialized later

        """
        try:
            if 'rubric' in response:
                rubric = response['rubric']
                rubric_renderer = CombinedOpenEndedRubric(self.render_template, view_only)
                rubric_dict = rubric_renderer.render_rubric(rubric)
                success = rubric_dict['success']
                rubric_html = rubric_dict['html']
                response['rubric'] = rubric_html
            return response
        # if we can't parse the rubric into HTML,
        except (etree.XMLSyntaxError, RubricParsingError):
            #This is a dev_facing_error
            log.exception("Cannot parse rubric string. Raw string: {0}".format(response['rubric']))
            return {'success': False,
                    'error': 'Error displaying submission'}
        except ValueError:
            #This is a dev_facing_error
            log.exception("Error parsing response: {0}".format(response))
            return {'success': False,
                    'error': "Error displaying submission"}
