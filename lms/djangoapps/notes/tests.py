"""
Unit tests for the notes API and model.
"""

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from collections import namedtuple
from random import random
import json
import logging

from . import utils, api, models

class UtilsTest(TestCase):
    def setUp(self): 
        ''' 
        Setup a dummy course-like object with a tabs field that can be
        accessed via attribute lookup. 
        '''
        self.course = namedtuple('DummyCourse', ['tabs'])
        self.course.tabs = []

    def test_notes_not_enabled(self):
        '''
        Tests that notes are disabled when the course tab configuration does NOT
        contain a tab with type "notes."
        '''
        self.assertFalse(utils.notes_enabled_for_course(self.course))

    def test_notes_enabled(self):
        '''
        Tests that notes are enabled when the course tab configuration contains
        a tab with type "notes."
        '''
        self.course.tabs = [
                {'type': 'foo'},
                {'name': 'My Notes', 'type': 'notes'},
                {'type':'bar'}]

        self.assertTrue(utils.notes_enabled_for_course(self.course))

class ApiTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Mocks
        api.api_enabled = (lambda request, course_id: True)

        # Create two accounts
        self.password = 'abc'
        self.student = User.objects.create_user('student', 'student@test.com', self.password)
        self.instructor = User.objects.create_user('instructor', 'instructor@test.com', self.password)
        self.course_id = 'HarvardX/CB22x/The_Ancient_Greek_Hero'
        self.note = {
            'user':self.student,
            'course_id':self.course_id,
            'uri':'/',
            'text':'foo',
            'quote':'bar',
            'range_start':0,
            'range_start_offset':0,
            'range_end':100,
            'range_end_offset':0,
            'tags':'a,b,c'
        }

    def login(self):
        self.client.login(username=self.student.username, password=self.password)

    def url(self, name):
        return reverse(name, kwargs={'course_id':self.course_id})

    def create_notes(self, num_notes):
        notes = [ models.Note(**self.note) for n in range(num_notes) ]
        models.Note.objects.bulk_create(notes)
        return notes

    def test_root(self):
        self.login()

        resp = self.client.get(self.url('notes_api_root'))
        self.assertEqual(resp.status_code, 200) 
        self.assertNotEqual(resp.content, '')

        content = json.loads(resp.content)

        self.assertEqual(set(('name','version')), set(content.keys()))
        self.assertIsInstance(content['version'], int)
        self.assertEqual(content['name'], 'Notes API')

    def test_index_empty(self):
        self.login()

        resp = self.client.get(self.url('notes_api_notes'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.content, '')

        content = json.loads(resp.content)
        self.assertEqual(len(content), 0)

    def test_index_with_notes(self):
        num_notes = 7
        self.login()
        self.create_notes(num_notes)

        resp = self.client.get(self.url('notes_api_notes'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.content, '')

        content = json.loads(resp.content)
        self.assertEqual(len(content), num_notes)

    def test_index_max_notes(self):
        self.login()

        MAX_LIMIT = api.API_SETTINGS.get('MAX_NOTE_LIMIT') 
        num_notes = MAX_LIMIT + 1
        self.create_notes(num_notes)

        resp = self.client.get(self.url('notes_api_notes'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.content, '')

        content = json.loads(resp.content)
        self.assertEqual(len(content), MAX_LIMIT)
