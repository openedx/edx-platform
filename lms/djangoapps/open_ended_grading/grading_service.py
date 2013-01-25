# This class gives a common interface for logging into the grading controller
import json
import logging
import requests
from requests.exceptions import RequestException, ConnectionError, HTTPError
import sys

from django.conf import settings
from django.http import HttpResponse, Http404

from courseware.access import has_access
from util.json_request import expect_json
from xmodule.course_module import CourseDescriptor
from xmodule.combined_open_ended_rubric import CombinedOpenEndedRubric
from lxml import etree
from mitxmako.shortcuts import render_to_string
from xmodule.x_module import ModuleSystem

log = logging.getLogger(__name__)

class GradingServiceError(Exception):
    pass

class GradingService(object):
    """
    Interface to staff grading backend.
    """
    def __init__(self, config):
        self.username = config['username']
        self.password = config['password']
        self.url = config['url']
        self.login_url = self.url + '/login/'
        self.session = requests.session()
        self.system = ModuleSystem(None, None, None, render_to_string, None)

    def _login(self):
        """
        Log into the staff grading service.

        Raises requests.exceptions.HTTPError if something goes wrong.

        Returns the decoded json dict of the response.
        """
        response = self.session.post(self.login_url,
                                     {'username': self.username,
                                      'password': self.password,})

        response.raise_for_status()

        return response.json

    def post(self, url, data, allow_redirects=False): 
        """
        Make a post request to the grading controller
        """
        try:
            op = lambda: self.session.post(url, data=data,
                                           allow_redirects=allow_redirects)
            r = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text

    def get(self, url, params, allow_redirects=False):
        """
        Make a get request to the grading controller
        """
        log.debug(params)
        op = lambda: self.session.get(url,
                                      allow_redirects=allow_redirects,
                                      params=params)
        try:
            r = self._try_with_login(op)
        except (RequestException, ConnectionError, HTTPError) as err:
            # reraise as promised GradingServiceError, but preserve stacktrace.
            raise GradingServiceError, str(err), sys.exc_info()[2]

        return r.text
        

    def _try_with_login(self, operation):
        """
        Call operation(), which should return a requests response object.  If
        the request fails with a 'login_required' error, call _login() and try
        the operation again.

        Returns the result of operation().  Does not catch exceptions.
        """
        response = operation()
        if (response.json
            and response.json.get('success') == False
            and response.json.get('error') == 'login_required'):
            # apparrently we aren't logged in.  Try to fix that.
            r = self._login()
            if r and not r.get('success'):
                log.warning("Couldn't log into staff_grading backend. Response: %s",
                            r)
            # try again
            response = operation()
            response.raise_for_status()

        return response

    def _render_rubric(self, response, view_only=False):
        """
        Given an HTTP Response with the key 'rubric', render out the html
        required to display the rubric
        """
        try:
            response_json = json.loads(response)
            if response_json.has_key('rubric'):
                rubric = response_json['rubric']
                rubric_renderer = CombinedOpenEndedRubric(self.system, False)
                success, rubric_html = rubric_renderer.render_rubric(rubric)
                if not success:
                    error_message = "Could not render rubric: {0}".format(rubric)
                    log.exception(error_message)
                    return json.dumps({'success': False,
                                       'error': error_message})
                response_json['rubric'] = rubric_html
            return json.dumps(response_json)
        # if we can't parse the rubric into HTML, 
        except etree.XMLSyntaxError:
            log.exception("Cannot parse rubric string. Raw string: {0}"
                          .format(rubric))
            return json.dumps({'success': False,
                               'error': 'Error displaying submission'})


