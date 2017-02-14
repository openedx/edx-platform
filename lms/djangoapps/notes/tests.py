"""
Unit tests for the notes app.
"""

from mock import patch, Mock

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

import json

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tabs import get_course_tab_list, CourseTab
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from notes import utils, api, models


class UtilsTest(ModuleStoreTestCase):
    """ Tests for the notes utils. """
    def setUp(self):
        '''
        Setup a dummy course-like object with a tabs field that can be
        accessed via attribute lookup.
        '''
        super(UtilsTest, self).setUp()
        self.course = CourseFactory.create()

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
        with self.settings(FEATURES={'ENABLE_STUDENT_NOTES': True}):
            self.course.advanced_modules = ["notes"]
            self.assertTrue(utils.notes_enabled_for_course(self.course))


class CourseTabTest(ModuleStoreTestCase):
    """
    Test that the course tab shows up the way we expect.
    """
    def setUp(self):
        '''
        Setup a dummy course-like object with a tabs field that can be
        accessed via attribute lookup.
        '''
        super(CourseTabTest, self).setUp()
        self.course = CourseFactory.create()
        self.user = UserFactory()
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)

    def enable_notes(self):
        """Enable notes and add the tab to the course."""
        self.course.tabs.append(CourseTab.load("notes"))
        self.course.advanced_modules = ["notes"]

    def has_notes_tab(self, course, user):
        """ Returns true if the current course and user have a notes tab, false otherwise. """
        request = RequestFactory().request()
        request.user = user
        all_tabs = get_course_tab_list(request, course)
        return any([tab.name == u'My Notes' for tab in all_tabs])

    def test_course_tab_not_visible(self):
        # module not enabled in the course
        self.assertFalse(self.has_notes_tab(self.course, self.user))

        with self.settings(FEATURES={'ENABLE_STUDENT_NOTES': False}):
            # setting not enabled and the module is not enabled
            self.assertFalse(self.has_notes_tab(self.course, self.user))

            # module is enabled and the setting is not enabled
            self.course.advanced_modules = ["notes"]
            self.assertFalse(self.has_notes_tab(self.course, self.user))

    def test_course_tab_visible(self):
        self.enable_notes()
        self.assertTrue(self.has_notes_tab(self.course, self.user))
        self.course.advanced_modules = []
        self.assertFalse(self.has_notes_tab(self.course, self.user))


class ApiTest(TestCase):

    def setUp(self):
        super(ApiTest, self).setUp()
        self.client = Client()

        # Mocks
        patcher = patch.object(api, 'api_enabled', Mock(return_value=True))
        patcher.start()
        self.addCleanup(patcher.stop)

        # Create two accounts
        self.password = 'abc'
        self.student = User.objects.create_user('student', 'student@test.com', self.password)
        self.student2 = User.objects.create_user('student2', 'student2@test.com', self.password)
        self.instructor = User.objects.create_user('instructor', 'instructor@test.com', self.password)
        self.course_key = SlashSeparatedCourseKey('HarvardX', 'CB22x', 'The_Ancient_Greek_Hero')
        self.note = {
            'user': self.student,
            'course_id': self.course_key,
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

    def login(self, as_student=None):
        username = None
        password = self.password

        if as_student is None:
            username = self.student.username
        else:
            username = as_student.username

        self.client.login(username=username, password=password)

    def url(self, name, args={}):
        args.update({'course_id': self.course_key.to_deprecated_string()})
        return reverse(name, kwargs=args)

    def create_notes(self, num_notes, create=True):
        notes = []
        for __ in range(num_notes):
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
            self.assertEqual(resp.status_code, 400)

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
        self.assertEqual(resp.status_code, 400)

    def test_read_note(self):
        self.login()

        notes = self.create_notes(3)
        self.assertEqual(len(notes), 3)

        for note in notes:
            resp = self.client.get(self.url('notes_api_note', {'note_id': note.pk}))
            self.assertEqual(resp.status_code, 200)
            self.assertNotEqual(resp.content, '')

            content = json.loads(resp.content)
            self.assertEqual(content['id'], note.pk)
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
        resp = self.client.get(self.url('notes_api_note', {'note_id': note.pk}))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.content, '')

    def test_delete_note(self):
        self.login()

        notes = self.create_notes(1)
        self.assertEqual(len(notes), 1)
        note = notes[0]

        resp = self.client.delete(self.url('notes_api_note', {
            'note_id': note.pk
        }))
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, '')

        with self.assertRaises(models.Note.DoesNotExist):
            models.Note.objects.get(pk=note.pk)

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
            'note_id': note.pk
        }))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.content, '')

        try:
            models.Note.objects.get(pk=note.pk)
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
        resp = self.client.put(self.url('notes_api_note', {'note_id': note.pk}),
                               json.dumps(updated_dict),
                               content_type='application/json',
                               HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(resp.status_code, 303)
        self.assertEqual(resp.content, '')

        actual = models.Note.objects.get(pk=note.pk)
        actual_dict = actual.as_dict()
        for field in ['text', 'tags']:
            self.assertEqual(actual_dict[field], updated_dict[field])

    def test_search_note_params(self):
        self.login()

        total = 3
        notes = self.create_notes(total)
        invalid_uri = ''.join([note.uri for note in notes])

        tests = [{'limit': 0, 'offset': 0, 'expected_rows': total},
                 {'limit': 0, 'offset': 2, 'expected_rows': total - 2},
                 {'limit': 0, 'offset': total, 'expected_rows': 0},
                 {'limit': 1, 'offset': 0, 'expected_rows': 1},
                 {'limit': 2, 'offset': 0, 'expected_rows': 2},
                 {'limit': total, 'offset': 2, 'expected_rows': 1},
                 {'limit': total, 'offset': total, 'expected_rows': 0},
                 {'limit': total + 1, 'offset': total + 1, 'expected_rows': 0},
                 {'limit': total + 1, 'offset': 0, 'expected_rows': total},
                 {'limit': 0, 'offset': 0, 'uri': invalid_uri, 'expected_rows': 0, 'expected_total': 0}]

        for test in tests:
            params = dict([(k, str(test[k]))
                          for k in ('limit', 'offset', 'uri')
                          if k in test])
            resp = self.client.get(self.url('notes_api_search'),
                                   params,
                                   content_type='application/json',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')

            self.assertEqual(resp.status_code, 200)
            self.assertNotEqual(resp.content, '')

            content = json.loads(resp.content)

            for expected_key in ('total', 'rows'):
                self.assertIn(expected_key, content)

            if 'expected_total' in test:
                self.assertEqual(content['total'], test['expected_total'])
            else:
                self.assertEqual(content['total'], total)

            self.assertEqual(len(content['rows']), test['expected_rows'])

            for row in content['rows']:
                self.assertIn('id', row)


class NoteTest(TestCase):
    def setUp(self):
        super(NoteTest, self).setUp()

        self.password = 'abc'
        self.student = User.objects.create_user('student', 'student@test.com', self.password)
        self.course_key = SlashSeparatedCourseKey('HarvardX', 'CB22x', 'The_Ancient_Greek_Hero')
        self.note = {
            'user': self.student,
            'course_id': self.course_key,
            'uri': '/',
            'text': 'foo',
            'quote': 'bar',
            'range_start': 0,
            'range_start_offset': 0,
            'range_end': 100,
            'range_end_offset': 0,
            'tags': 'a,b,c'
        }

    def test_clean_valid_note(self):
        reference_note = models.Note(**self.note)
        body = reference_note.as_dict()

        note = models.Note(course_id=self.course_key, user=self.student)
        try:
            note.clean(json.dumps(body))
            self.assertEqual(note.uri, body['uri'])
            self.assertEqual(note.text, body['text'])
            self.assertEqual(note.quote, body['quote'])
            self.assertEqual(note.range_start, body['ranges'][0]['start'])
            self.assertEqual(note.range_start_offset, body['ranges'][0]['startOffset'])
            self.assertEqual(note.range_end, body['ranges'][0]['end'])
            self.assertEqual(note.range_end_offset, body['ranges'][0]['endOffset'])
            self.assertEqual(note.tags, ','.join(body['tags']))
        except ValidationError:
            self.fail('a valid note should not raise an exception')

    def test_clean_invalid_note(self):
        note = models.Note(course_id=self.course_key, user=self.student)
        for empty_type in (None, '', 0, []):
            with self.assertRaises(ValidationError):
                note.clean(None)

        with self.assertRaises(ValidationError):
            note.clean(json.dumps({
                'text': 'foo',
                'quote': 'bar',
                'ranges': [{} for __ in range(10)]  # too many ranges
            }))

    def test_as_dict(self):
        note = models.Note(course_id=self.course_key, user=self.student)
        d = note.as_dict()
        self.assertNotIsInstance(d, basestring)
        self.assertEqual(d['user_id'], self.student.id)
        self.assertNotIn('course_id', d)
