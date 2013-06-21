from django.test import TestCase

from django_comment_client.helpers import pluralize


class PluralizeTestCase(TestCase):

    def testPluralize(self):
        self.term = "cat"
        self.assertEqual(pluralize(self.term, 0), "cats")
        self.assertEqual(pluralize(self.term, 1), "cat")
        self.assertEqual(pluralize(self.term, 2), "cats")
