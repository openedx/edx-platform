"""
Tests for deprecated xblocks in XBlockDisableConfig.
"""
import ddt

from mock import patch
from django.test import TestCase
from xblock_django.models import XBlockDisableConfig


@ddt.ddt
class XBlockDisableConfigTestCase(TestCase):
    """
    Tests for the DjangoXBlockUserService.
    """
    def setUp(self):
        super(XBlockDisableConfigTestCase, self).setUp()

        # Initialize the deprecated modules settings with empty list
        XBlockDisableConfig.objects.create(
            disabled_blocks='', enabled=True
        )

    @ddt.data(
        ('poll', ['poll']),
        ('poll survey annotatable textannotation', ['poll', 'survey', 'annotatable', 'textannotation']),
        ('', [])
    )
    @ddt.unpack
    def test_deprecated_blocks_splitting(self, xblocks, expected_result):
        """
        Tests that it correctly splits the xblocks defined in field.
        """
        XBlockDisableConfig.objects.create(
            disabled_create_blocks=xblocks, enabled=True
        )

        self.assertEqual(
            XBlockDisableConfig.disabled_create_block_types(), expected_result
        )

    @patch('django.conf.settings.DEPRECATED_ADVANCED_COMPONENT_TYPES', ['poll', 'survey'])
    def test_deprecated_blocks_file(self):
        """
        Tests that deprecated modules contain entries from settings file DEPRECATED_ADVANCED_COMPONENT_TYPES
        """
        self.assertEqual(XBlockDisableConfig.disabled_create_block_types(), ['poll', 'survey'])

    @patch('django.conf.settings.DEPRECATED_ADVANCED_COMPONENT_TYPES', ['poll', 'survey'])
    def test_deprecated_blocks_file_and_config(self):
        """
        Tests that deprecated types defined in both settings and config model are read.
        """
        XBlockDisableConfig.objects.create(
            disabled_create_blocks='annotatable', enabled=True
        )

        self.assertEqual(XBlockDisableConfig.disabled_create_block_types(), ['annotatable', 'poll', 'survey'])
