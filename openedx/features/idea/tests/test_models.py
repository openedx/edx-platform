from ddt import data, ddt, unpack
from django.db import DataError, IntegrityError
from django.test import TestCase

from common.test.utils import MockS3Mixin
from openedx.features.idea.constants import CITY_MAX_LENGTH, OVERVIEW_MAX_LENGTH, TITLE_MAX_LENGTH
from openedx.features.idea.models import Idea

from .factories import IdeaFactory


@ddt
class IdeaModelTest(MockS3Mixin, TestCase):
    """Test cases for Idea model"""

    def test_save_idea_model_with_mandatory_fields_successfully(self):
        """Create an idea, and assert that it is saved successfully with all mandatory data"""
        idea = IdeaFactory()

        idea_from_database = Idea.objects.get(pk=idea.id)

        self.assertIsNotNone(idea_from_database)
        self.assertEqual(idea.title, idea_from_database.title)

    def test_location_from_city_and_country(self):
        """Create an idea and assert that location property is accessible in specific format"""
        idea = IdeaFactory(country='PK', city='Lahore')
        self.assertIsNotNone(idea.location, 'Lahore, Pakistan')

    @data('user', 'title', 'overview', 'description', 'organization',
          'organization_mission', 'country', 'city')
    def test_required_fields(self, field_name):
        """Create idea for each required field and assert that idea fail to save if that field is not provided"""
        with self.assertRaises(IntegrityError):
            IdeaFactory(**{field_name: None})

    @data(['city', CITY_MAX_LENGTH], ['overview', OVERVIEW_MAX_LENGTH], ['title', TITLE_MAX_LENGTH])
    @unpack
    def test_max_length(self, field_name, max_length):
        """
        Create idea for each field which has max length limit and
        assert that idea fail to save if max length limit exceeds
        """
        with self.assertRaises(DataError):
            string_exceeding_max_limit = 'n' * (max_length + 1)
            IdeaFactory(**{field_name: string_exceeding_max_limit})

    def test_visual_attachments(self):
        """Create idea with visual attachments and verify that it saves successfully"""
        idea = IdeaFactory(
            image='my_image.jpg',
            file='my_file.docx',
            video_link='https://example.com'
        )

        idea_from_databased = Idea.objects.get(pk=idea.id)

        self.assertIsNotNone(idea_from_databased)
        self.assertIsNotNone(idea.image)
        self.assertIsNotNone(idea.file)
        self.assertEqual(idea.image.name, idea_from_databased.image.name)
        self.assertEqual(idea.file.name, idea_from_databased.file.name)
        self.assertEqual(idea.video_link, idea_from_databased.video_link)
