# -*- coding: utf-8 -*-
"""
Module for Completion Aggregate API page
"""

import json

from bok_choy.page_object import PageObject
from common.test.acceptance.pages.lms import BASE_URL


class CompletionAggregatePage(PageObject):
    """
    Visit this page to view the completion aggregate data list.
    """
    def __init__(self, browser, username=None, course_id=None):
        """Initialize the page.

        Arguments:
            browser (Browser): The browser instance.
            username: username of the user for which we want the completion aggregate
            course_id: course key of the course
        """
        super(CompletionAggregatePage, self).__init__(browser)
        self.username = username
        self.course_id = course_id
        self.aggregate_list_dict = None

    @property
    def url(self):
        """
        Construct a URL to the page
        """
        url = BASE_URL + '/completion-aggregator/v1/course/'

        if self.course_id:
            url = url + self.course_id + '/'

        if self.username:
            url = url + '?username=' + self.username

        return url

    def is_browser_on_page(self):

        body = self.q(css='BODY').text[0]
        try:
            self.aggregate_list_dict = json.loads(body)
            return 'results' in self.aggregate_list_dict

        except ValueError:
            return False

    def get_completion_data(self):
        return self.aggregate_list_dict['results'][0]['completion']
