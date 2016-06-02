"""
Tests for deprecated xblocks in XBlockDisableConfig.
"""
import ddt

from mock import patch
from django.test import TestCase
from xblock_django.models import XBlockDisableConfig, XBlockConfig


# @ddt.ddt
# class XBlockDisableConfigTestCase(TestCase):
#     """
#     Tests for the DjangoXBlockUserService.
#     """
#     def setUp(self):
#         super(XBlockDisableConfigTestCase, self).setUp()
#
#         # Initialize the deprecated modules settings with empty list
#         XBlockDisableConfig.objects.create(
#             disabled_blocks='', enabled=True
#         )
#
#     @ddt.data(
#         ('poll', ['poll']),
#         ('poll survey annotatable textannotation', ['poll', 'survey', 'annotatable', 'textannotation']),
#         ('', [])
#     )
#     @ddt.unpack
#     def test_deprecated_blocks_splitting(self, xblocks, expected_result):
#         """
#         Tests that it correctly splits the xblocks defined in field.
#         """
#         XBlockDisableConfig.objects.create(
#             disabled_create_blocks=xblocks, enabled=True
#         )
#
#         self.assertEqual(
#             XBlockDisableConfig.disabled_create_block_types(), expected_result
#         )
#
#     @patch('django.conf.settings.DEPRECATED_ADVANCED_COMPONENT_TYPES', ['poll', 'survey'])
#     def test_deprecated_blocks_file(self):
#         """
#         Tests that deprecated modules contain entries from settings file DEPRECATED_ADVANCED_COMPONENT_TYPES
#         """
#         self.assertEqual(XBlockDisableConfig.disabled_create_block_types(), ['poll', 'survey'])
#
#     @patch('django.conf.settings.DEPRECATED_ADVANCED_COMPONENT_TYPES', ['poll', 'survey'])
#     def test_deprecated_blocks_file_and_config(self):
#         """
#         Tests that deprecated types defined in both settings and config model are read.
#         """
#         XBlockDisableConfig.objects.create(
#             disabled_create_blocks='annotatable', enabled=True
#         )
#
#         self.assertEqual(XBlockDisableConfig.disabled_create_block_types(), ['annotatable', 'poll', 'survey'])


class XBlockConfigTestCase(TestCase):

    def tearDown(self):
        super(XBlockConfigTestCase, self).tearDown()
        XBlockConfig.objects.all().delete()

    def test_deprecated_blocks(self):
        XBlockConfig.objects.create(
            name="poll",
            support_level=XBlockConfig.UNSUPPORTED_NO_OPT_IN,
            deprecated=True
        )

        XBlockConfig.objects.create(
            name="survey",
            support_level=XBlockConfig.DISABLED,
            deprecated=True
        )

        XBlockConfig.objects.create(
            name="done",
            support_level=XBlockConfig.FULL_SUPPORT
        )

        deprecated_xblock_names = [block.name for block in XBlockConfig.deprecated_xblocks()]
        self.assertEqual(["poll", "survey"], deprecated_xblock_names)

    def test_disabled_blocks(self):
        XBlockConfig.objects.create(
            name="poll",
            support_level=XBlockConfig.UNSUPPORTED_NO_OPT_IN,
            deprecated=True
        )

        XBlockConfig.objects.create(
            name="survey",
            support_level=XBlockConfig.DISABLED,
            deprecated=True
        )

        XBlockConfig.objects.create(
            name="annotatable",
            support_level=XBlockConfig.DISABLED,
            deprecated=False
        )

        XBlockConfig.objects.create(
            name="done",
            support_level=XBlockConfig.FULL_SUPPORT
        )

        disabled_xblock_names = [block.name for block in XBlockConfig.disabled_xblocks()]
        self.assertEqual(["survey", "annotatable"], disabled_xblock_names)

    def test_authorable_blocks(self):
        XBlockConfig.objects.create(
            name="problem",
            support_level=XBlockConfig.FULL_SUPPORT
        )

        XBlockConfig.objects.create(
            name="problem",
            support_level=XBlockConfig.FULL_SUPPORT,
            template="multiple_choice"
        )

        XBlockConfig.objects.create(
            name="html",
            support_level=XBlockConfig.PROVISIONAL_SUPPORT,
            template="zoom"
        )

        XBlockConfig.objects.create(
            name="split_module",
            support_level=XBlockConfig.UNSUPPORTED_OPT_IN,
            deprecated=True
        )

        XBlockConfig.objects.create(
            name="poll",
            support_level=XBlockConfig.UNSUPPORTED_NO_OPT_IN,
            deprecated=True
        )

        XBlockConfig.objects.create(
            name="survey",
            support_level=XBlockConfig.DISABLED,
        )

        authorable_xblock_names = [block.name for block in XBlockConfig.authorable_xblocks()]
        self.assertEqual(["problem", "problem"], authorable_xblock_names)

        authorable_xblock_names = [block.name for block in XBlockConfig.authorable_xblocks(limited_support_opt_in=True)]
        self.assertEqual(["problem", "problem", "html", "split_module"], authorable_xblock_names)

        authorable_xblocks = XBlockConfig.authorable_xblocks(name="problem", limited_support_opt_in=True)
        self.assertEqual(2, len(authorable_xblocks))
        self.assertEqual("problem", authorable_xblocks[0].name)
        self.assertEqual("", authorable_xblocks[0].template)
        self.assertEqual("problem", authorable_xblocks[1].name)
        self.assertEqual("multiple_choice", authorable_xblocks[1].template)

        authorable_xblocks = XBlockConfig.authorable_xblocks(name="html", limited_support_opt_in=True)
        self.assertEqual(1, len(authorable_xblocks))
        self.assertEqual("html", authorable_xblocks[0].name)
        self.assertEqual("zoom", authorable_xblocks[0].template)

        authorable_xblocks = XBlockConfig.authorable_xblocks(name="video")
        self.assertEqual(0, len(authorable_xblocks))
