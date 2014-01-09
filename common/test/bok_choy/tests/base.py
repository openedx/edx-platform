"""
Helpful base test case classes for testing the LMS.
"""

from bok_choy.web_app_test import WebAppTest
from .fixtures import UserFixture
from edxapp_pages.studio.login import LoginPage
from edxapp_pages.studio.index import DashboardPage
from edxapp_pages.studio.auto_auth import AutoAuthPage
from uuid import uuid4
import requests
import os
import re
import json

class StudioLoggedInTest(WebAppTest):
    """
    Tests that assume the user is logged in to a unique account.
    We use the auto_auth workflow for this.
    """

    @property
    def page_object_classes(self):
        return [AutoAuthPage]

    def setUp(self):
        """
        Each test begins after creating a user.
        """
        super(StudioLoggedInTest, self).setUp()
        self._login()

    def _login(self):
        """
        Use the auto-auth workflow to create the account and log in.
        Grab the csrftoken and sessionid so other browserless API requests
        can use the credentials.
        """
        self.ui.visit('studio.auto_auth')

        self.sessionid = ''
        self.csrftoken = ''
        cookies = self.ui._browser.cookies.all()
        for cookie in cookies:
            if cookie.get('name') == 'sessionid':
                self.sessionid = cookie.get('value')
            if cookie.get('name') == 'csrftoken':
                self.csrftoken = cookie.get('value')


class StudioWithCourseTest(StudioLoggedInTest):
    """
    Tests that assume the user is logged in to a unique account
    and has a sessionid and csrftoken.
    """

    def setUp(self):
        """
        Each test begins after creating a course and navigating
        to the dashboard page.
        """
        super(StudioWithCourseTest, self).setUp()
        self._create_course()

    def _create_course(self):
        """
        Create a Course
        """
        method = 'post'
        path = '/course'
        headers = {
            'content-type': 'application/json',
            'X-CSRFToken': self.csrftoken,
            'accept': 'application/json'
        }
        cookies = dict(csrftoken=self.csrftoken, sessionid=self.sessionid)

        course_num = '{}'.format(uuid4().hex[:4])
        org = 'OrgX'
        display_name = 'Test Course {}'.format(course_num)
        run = '2014'
        data = {'org': org, 'number': course_num, 'display_name': display_name, 'run': run}
        self.course_id = '{}.{}.{}'.format(org, course_num, run)
        url = '{}{}'.format('http://localhost:8031', path)

        resp = requests.request(method, url, data=json.dumps(data), headers=headers, cookies=cookies)
