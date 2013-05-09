"""
Unit tests for the notes app.
"""

from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

import collections
import unittest
import json
import logging

from . import utils, api, models


class UtilsTest(TestCase):
    def setUp(self):
        '''
        Setup a dummy course-like object with a tabs field that can be
        accessed via attribute lookup.
        '''
        self.course = collections.namedtuple('DummyCourse', ['tabs'])
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
        self.course.tabs = [{'type': 'foo'},
                            {'name': 'My Notes', 'type': 'notes'},
                            {'type': 'bar'}]

        self.assertTrue(utils.notes_enabled_for_course(self.course))


class ApiTest(TestCase):

    def setUp(self):
        self.client = Client()

        # Mocks
        api.api_enabled = self.mock_api_enabled(True)

        # Create two accounts
        self.password = 'abc'
        self.student = User.objects.create_user('student', 'student@test.com', self.password)
        self.student2 = User.objects.create_user('student2', 'student2@test.com', self.password)
        self.instructor = User.objects.create_user('instructor', 'instructor@test.com', self.password)
        self.course_id = 'HarvardX/CB22x/The_Ancient_Greek_Hero'
        self.note = {
            'user': self.student,
            'course_id': self.course_id,
            'uri': '/',
            'text': 'foo',
            'quote': 'bar',
            'range_start': 0,
            'range_start_offset': 0,
            'range_end': 100,
            'range_end_offset': 0,
            'tags': 'a,b,c'
        }

        # Make sure no note with this ID ever exists for testing purposes
        self.NOTE_ID_DOES_NOT_EXIST = 99999

    def mock_api_enabled(self, is_enabled):
        return (lambda request, course_id: is_enabled)

    def login(self, as_student=None):
        username = None
        password = self.password

        if as_student is None:
            username = self.student.username
        else:
            username = as_student.username

        self.client.login(username=username, password=password)

    def url(self, name, args={}):
        args.update({'course_id': self.course_id})
        return reverse(name, kwargs=args)

    def create_notes(self, num_notes, create=True):
        notes = []
        for n in range(num_notes):
            note = models.Note(**self.note)
            if create:
                note.save()
            notes.append(note)
        return notes

    def test_root(self):
        self.login()

        resp = self.client.get(self.url('notes_api_root'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.content, '')

        content = json.loads(resp.content)

        self.assertEqual(set(('name', 'version')), set(content.keys()))
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
        num_notes = 3
        self.login()
        self.create_notes(num_notes)

        resp = self.client.get(self.url('notes_api_notes'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(resp.content, '')

        content = json.loads(resp.content)
        self.assertIsInstance(content, list)
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
        self.assertIsInstance(content, list)
        self.assertEqual(len(content), MAX_LIMIT)

    def test_create_note(self):
        self.login()

        notes = self.create_notes(1)
        self.assertEqual(len(notes), 1)

        note_dict = notes[0].as_dict()
        excluded_fields = ['id', 'user_id', 'created', 'updated']
        note = dict([(k, v) for k, v in note_dict.items() if k not in excluded_fields])

        resp = self.client.post(self.url('notes_api_notes'),
                                json.dumps(note),
                                content_type='application/json',
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(resp.status_code, 303)
        self.assertEqual(len(resp.content), 0)

    def test_create_empty_notes(self):
        self.login()

        for empty_test in [None, [], '']:
            resp = self.client.post(self.url('notes_api_notes'),
                                    json.dumps(empty_test),
                                    content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            self.assertEqual(resp.status_code, 500)

    def test_create_note_missing_ranges(self):
        self.login()

        notes = self.create_notes(1)
        self.assertEqual(len(notes), 1)
        note_dict = notes[0].as_dict()

        excluded_fields = ['id', 'user_id', 'created', 'updated'] + ['ranges']
        note = dict([(k, v) for k, v in note_dict.items() if k not in excluded_fields])

        resp = self.client.post(self.url('notes_api_notes'),
                                json.dumps(note),
                                content_type='application/json',
                                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 500)

    def test_read_note(self):
        self.login()

        notes = self.create_notes(3)
        self.assertEqual(len(notes), 3)

        for note in notes:
            resp = self.client.get(self.url('notes_api_note', {'note_id': note.id}))
            self.assertEqual(resp.status_code, 200)
            self.assertNotEqual(resp.content, '')

            content = json.loads(resp.content)
            self.assertEqual(content['id'], note.id)
            self.assertEqual(content['user_id'], note.user_id)

    def test_note_doesnt_exist_to_read(self):
        self.login()
        resp = self.client.get(self.url('notes_api_note', {
            'note_id': self.NOTE_ID_DOES_NOT_EXIST
        }))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content, '')

    def test_student_doesnt_have_permission_to_read_note(self):
        notes = self.create_notes(1)
        self.assertEqual(len(notes), 1)
        note = notes[0]

        # set the student id to a different student (not the one that created the notes)
        self.login(as_student=self.student2)
        resp = self.client.get(self.url('notes_api_note', {'note_id': note.id}))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.content, '')

    def test_delete_note(self):
        self.login()

        notes = self.create_notes(1)
        self.assertEqual(len(notes), 1)
        note = notes[0]

        resp = self.client.delete(self.url('notes_api_note', {
            'note_id': note.id
        }))
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, '')

        with self.assertRaises(models.Note.DoesNotExist):
            models.Note.objects.get(pk=note.id)

    def test_note_does_not_exist_to_delete(self):
        self.login()

        resp = self.client.delete(self.url('notes_api_note', {
            'note_id': self.NOTE_ID_DOES_NOT_EXIST
        }))
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.content, '')

    def test_student_doesnt_have_permission_to_delete_note(self):
        notes = self.create_notes(1)
        self.assertEqual(len(notes), 1)
        note = notes[0]

        self.login(as_student=self.student2)
        resp = self.client.delete(self.url('notes_api_note', {
            'note_id': note.id
        }))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.content, '')

        try:
            models.Note.objects.get(pk=note.id)
        except models.Note.DoesNotExist:
            self.fail('note should exist and not be deleted because the student does not have permission to do so')

    def test_update_note(self):
        notes = self.create_notes(1)
        note = notes[0]

        updated_dict = note.as_dict()
        updated_dict.update({
            'text': 'itchy and scratchy',
            'tags': ['simpsons', 'cartoons', 'animation']
        })

        self.login()
        resp = self.client.put(self.url('notes_api_note', {'note_id': note.id}),
                               json.dumps(updated_dict),
                               content_type='application/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 303)
        self.assertEqual(resp.content, '')

        actual = models.Note.objects.get(pk=note.id)
        actual_dict = actual.as_dict()
        for field in ['text', 'tags']:
            self.assertEqual(actual_dict[field], updated_dict[field])

    @unittest.skip("skipping search test stub")
    def test_search_note(self):
        pass
