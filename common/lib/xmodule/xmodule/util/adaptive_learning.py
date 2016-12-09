# -*- coding: utf-8 -*-
"""
Utilities for adaptive learning features.
"""

import hashlib
import json
import logging
import requests

from lazy import lazy

log = logging.getLogger(__name__)


class AdaptiveLearningConfiguration(object):
    """
    Stores configuration that is necessary for interacting with external services
    that provide adaptive learning features.
    """

    def __init__(self, **kwargs):
        """
        Creates an attribute for each key in `kwargs` and sets it to the corresponding value.
        """
        self._configuration = kwargs
        for attr, value in kwargs.items():
            setattr(self, attr, value)

    def __str__(self):
        """
        Returns string listing all custom attributes set on `self`.
        """
        return str(self._configuration)

    @staticmethod
    def is_meaningful(configuration):
        """
        Return True if `configuration` has meaningful values for all relevant settings,
        else False.

        If `configuration` is empty, return False as well.
        """
        if not configuration:
            return False

        is_meaningful = True
        for val in configuration.values():
            if isinstance(val, str):
                is_meaningful &= bool(val)  # Empty strings are not considered meaningful
            elif isinstance(val, int):
                is_meaningful &= (val >= 0)  # Negative ints are not considered meaningful
        return is_meaningful


class AdaptiveLearningAPIMixin(object):
    """
    Provides low-level methods for interacting with external service that provides adaptive learning features.
    """

    @lazy
    def adaptive_learning_configuration(self):
        """
        Return configuration for accessing external service that provides adaptive learning features.

        This configuration is a course-wide setting, so classes using this mixin
        must instantiate objects with a specific course to read the configuration from.
        """
        return AdaptiveLearningConfiguration(
            **self._course.adaptive_learning_configuration
        )

    @lazy
    def adaptive_learning_url(self):
        """
        Return base URL for external service that provides adaptive learning features.

        The base URL is a combination of the URL (url) and API version (api_version)
        specified in the adaptive learning configuration of a course.
        """
        url = self.adaptive_learning_configuration.url
        api_version = self.adaptive_learning_configuration.api_version
        return '{url}/{api_version}'.format(url=url, api_version=api_version)

    @lazy
    def instance_url(self):
        """
        Return URL for requesting instance-specific data from external service
        that provides adaptive learning features.
        """
        instance_id = self.adaptive_learning_configuration.instance_id
        return '{base_url}/instances/{instance_id}'.format(
            base_url=self.adaptive_learning_url, instance_id=instance_id
        )

    @lazy
    def students_url(self):
        """
        Return URL for requests dealing with students.
        """
        return '{base_url}/students'.format(base_url=self.instance_url)

    @lazy
    def events_url(self):
        """
        Return URL for requests dealing with events.
        """
        return '{base_url}/events'.format(base_url=self.instance_url)

    @lazy
    def knowledge_node_students_url(self):
        """
        Return URL for accessing 'knowledge node student' objects.
        """
        return '{base_url}/knowledge_node_students'.format(base_url=self.instance_url)

    @lazy
    def pending_reviews_url(self):
        """
        Return URL for accessing pending reviews.
        """
        return '{base_url}/review_utils/fetch_pending_reviews_questions'.format(base_url=self.instance_url)

    @lazy
    def request_headers(self):
        """
        Return custom headers for requests to external service that provides adaptive learning features.
        """
        access_token = self.adaptive_learning_configuration.access_token
        return {
            'Authorization': 'Token token={access_token}'.format(access_token=access_token)
        }

    def get_knowledge_node_student_id(self, knowledge_node_uid, student_uid):
        """
        Return ID of 'knowledge node student' object linking student identified by `student_uid`
        to unit identified by `knowledge_node_uid`.
        """
        knowledge_node_student = self.get_or_create_knowledge_node_student(knowledge_node_uid, student_uid)
        return knowledge_node_student.get('id')

    def get_or_create_knowledge_node_student(self, knowledge_node_uid, student_uid):
        """
        Return 'knowledge node student' object for user identified by `student_uid`
        and unit identified by `knowledge_node_uid`.
        """
        # Create student
        self.get_or_create_student(student_uid)
        # Link student to unit
        knowledge_node_student = self.get_knowledge_node_student(knowledge_node_uid, student_uid)
        if knowledge_node_student is None:
            knowledge_node_student = self.create_knowledge_node_student(knowledge_node_uid, student_uid)
        return knowledge_node_student

    def get_or_create_student(self, student_uid):
        """
        Create a new student on external service if it doesn't exist,
        and return it.
        """
        student = self.get_student(student_uid)
        if student is None:
            student = self.create_student(student_uid)
        return student

    def get_student(self, student_uid):
        """
        Return external information about student identified by `student_uid`,
        or None if external service does not know about student.
        """
        url = self.generate_student_url(student_uid)
        payload = {'key_type': 'uid'}
        response = requests.get(url, headers=self.request_headers, data=payload)
        students = json.loads(response.content)
        if len(students) == 0:
            student = None
        elif len(students) == 1:
            student = students.pop(0)
        return student

    def create_student(self, student_uid):
        """
        Create student identified by `student_uid` on external service,
        and return it.
        """
        url = self.students_url
        payload = {'uid': student_uid}
        response = requests.post(url, headers=self.request_headers, data=payload)
        student = json.loads(response.content)
        return student

    def get_knowledge_node_student(self, knowledge_node_uid, student_uid):
        """
        Return 'knowledge node student' object for user identified by `student_uid`
        and unit identified by `knowledge_node_uid`, or None if it does not exist.
        """
        # Get 'knowledge node student' objects for user identified by `student_uid`
        links = self.get_knowledge_node_students(student_uid)
        # Filter them by `knowledge_node_uid`
        try:
            link = next(
                l for l in links if
                l.get('knowledge_node_uid') == knowledge_node_uid
            )
        except StopIteration:
            link = None
        return link

    def get_knowledge_node_students(self, student_uid):
        """
        Return list of all 'knowledge node student' objects for this course and user identified by `student_uid`.
        """
        url = self.knowledge_node_students_url
        payload = {'student_id': student_uid, 'key_type': 'uid'}
        response = requests.get(url, headers=self.request_headers, data=payload)
        links = json.loads(response.content)
        return links

    def create_knowledge_node_student(self, knowledge_node_uid, student_uid):
        """
        Create 'knowledge node student' object that links student identified by `student_uid`
        to unit identified by `knowledge_node_uid`, and return it.
        """
        url = self.knowledge_node_students_url
        payload = {'knowledge_node_uid': knowledge_node_uid, 'student_uid': student_uid}
        response = requests.post(url, headers=self.request_headers, data=payload)
        knowledge_node_student = json.loads(response.content)
        return knowledge_node_student

    def create_event(self, knowledge_node_uid, student_uid, event_type, **data):
        """
        Create event of type `event_type` for unit identified by `knowledge_node_uid`
        and student identified by `user_id`, sending any kwargs in `data` along with the default payload.
        """
        url = self.events_url
        knowledge_node_student_id = self.get_knowledge_node_student_id(knowledge_node_uid, student_uid)
        payload = {
            'knowledge_node_student_id': knowledge_node_student_id,
            'type': event_type,
        }
        payload.update(data)

        # Send request
        response = requests.post(url, headers=self.request_headers, data=payload)
        event = json.loads(response.content)
        return event

    def generate_student_url(self, student_uid):
        """
        Return URL for fetching information about student identified by `student_uid`.
        """
        return '{students_url}/{student_uid}'.format(students_url=self.students_url, student_uid=student_uid)

    def generate_student_uid(self, user_id):
        """
        Return student UID for user identified by `user_id`.

        Incorporate the following information when creating the digest:

        - Course ID of current course
        - Access token from adaptive learning configuration for current course
        """
        hasher = hashlib.md5()
        hasher.update(self.adaptive_learning_configuration.access_token)
        hasher.update(unicode(user_id))
        hasher.update(self._course.id.to_deprecated_string().encode('utf-8'))
        anonymous_user_id = hasher.hexdigest()
        return anonymous_user_id


class AdaptiveLearningAPIClient(AdaptiveLearningAPIMixin):
    """
    Handles communication with external service that provides adaptive learning features.
    """

    def __init__(self, course, *args, **kwargs):
        """
        Instantiate `AdaptiveLearningAPIClient` for `course`.
        """
        super(AdaptiveLearningAPIClient, self).__init__(*args, **kwargs)
        self._course = course

    # Public API

    def create_read_event(self, knowledge_node_uid, user_id):
        """
        Create read event for unit identified by `knowledge_node_uid` and student identified by `user_id`.
        """
        student_uid = self.generate_student_uid(user_id)
        return self.create_event(knowledge_node_uid, student_uid, 'EventRead')

    def create_result_event(self, knowledge_node_uid, user_id, result):
        """
        Create result event for unit identified by `knowledge_node_uid` and student identified by `user_id`
        using adaptive learning configuration from `course`.
        """
        student_uid = self.generate_student_uid(user_id)
        data = {'payload': result}
        return self.create_event(knowledge_node_uid, student_uid, 'EventResult', **data)

    def create_knowledge_node_students(self, knowledge_node_uids, user_id):
        """
        Create 'knowledge node student' objects that link student identified by `user_id`
        to review questions identified by block IDs listed in `knowledge_node_uids`, and return them.
        """
        student_uid = self.generate_student_uid(user_id)
        knowledge_node_students = []
        for knowledge_node_uid in knowledge_node_uids:
            knowledge_node_student = self.get_or_create_knowledge_node_student(knowledge_node_uid, student_uid)
            knowledge_node_students.append(knowledge_node_student)
        return knowledge_node_students

    def get_pending_reviews(self, user_id):
        """
        Return pending reviews for user identified by `user_id`.

        If external service does not know about user (because user is not enrolled in current course,
        or has never interacted with adaptive learning content in current course), return an empty list.
        """
        url = self.pending_reviews_url
        student_uid = self.generate_student_uid(user_id)
        payload = {'student_uid': student_uid, 'nested': True}
        response = requests.get(url, headers=self.request_headers, data=payload)
        if response.content == 'No Student Found':
            pending_reviews_user = []
        else:
            pending_reviews_user = json.loads(response.content)
        return pending_reviews_user
