import string
import random
import collections

from django.test import TestCase                         

import django_comment_client.mustache_helpers as mustache_helpers

class PluralizeTestCase(TestCase):

	def test_pluralize(self):
		self.text1 = '0 goat'
		self.text2 = '1 goat'
		self.text3 = '7 goat'
		self.content = 'unused argument'
		self.assertEqual(mustache_helpers.pluralize(self.content, self.text1), 'goats')
		self.assertEqual(mustache_helpers.pluralize(self.content, self.text2), 'goat')
		self.assertEqual(mustache_helpers.pluralize(self.content, self.text3), 'goats')

class CloseThreadTextTestCase(TestCase):
	
	def test_close_thread_text(self):
		self.contentClosed = {'closed': True}
		self.contentOpen = {'closed': False}
		self.assertEqual(mustache_helpers.close_thread_text(self.contentClosed), 'Re-open thread')
		self.assertEqual(mustache_helpers.close_thread_text(self.contentOpen), 'Close thread')
