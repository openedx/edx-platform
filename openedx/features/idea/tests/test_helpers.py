from django.test import TestCase

from openedx.features.idea.helpers import upload_to_path
from openedx.features.idea.models import Idea


class IdeaHelpersTest(TestCase):

    def test_upload_to_path(self):
        """Assert that file upload path is in specific format i.e. app_label/folder/filename"""
        expected_result = upload_to_path(Idea, 'my_file.jpg', 'images')
        self.assertEqual(expected_result, 'idea/images/my_file.jpg')
