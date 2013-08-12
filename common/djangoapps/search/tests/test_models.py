from django.test import TestCase
from search.models import _snippet_generator

TEST_TEXT = "Lorem ipsum dolor sit amet, consectetur adipisicing elit, \
            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris \
            nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in \
            reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. \
            Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia \
            deserunt mollit anim id est laborum"


class ModelTest(TestCase):

    def test_snippet_generation(self):
        snippets = _snippet_generator(TEST_TEXT, "quis nostrud", bold=False)
        self.assertTrue(snippets.startswith("Ut enim ad minim"))
        self.assertTrue(snippets.endswith("anim id est laborum"))

    def test_highlighting(self):
        highlights = _snippet_generator(TEST_TEXT, "quis nostrud")
        self.assertTrue(highlights.startswith("Ut enim ad minim"))
        self.assertTrue(highlights.strip().endswith("anim id est laborum"))
        self.assertTrue("<b class=highlight>quis</b>" in highlights)
        self.assertTrue("<b class=highlight>nostrud</b>" in highlights)
