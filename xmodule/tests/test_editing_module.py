""" Tests for editing descriptors"""


import logging
import os
import unittest
from unittest.mock import Mock

from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from pkg_resources import resource_string
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.editing_module import TabsEditingDescriptor
from xmodule.tests import get_test_descriptor_system

log = logging.getLogger(__name__)


class TabsEditingDescriptorTestCase(unittest.TestCase):
    """ Testing TabsEditingDescriptor"""

    def setUp(self):
        super().setUp()
        system = get_test_descriptor_system(render_template=Mock())
        self.tabs = [
            {
                'name': "Test_css",
                'template': "tabs/codemirror-edit.html",
                'current': True,
            },
            {
                'name': "Subtitles",
                'template': "video/subtitles.html",
            },
            {
                'name': "Settings",
                'template': "tabs/video-metadata-edit-tab.html"
            }
        ]

        TabsEditingDescriptor.tabs = self.tabs
        self.descriptor = system.construct_xblock_from_class(
            TabsEditingDescriptor,
            scope_ids=ScopeIds(None, None, None,
                               BlockUsageLocator(CourseLocator('org', 'course', 'run', branch='revision'),
                                                 'category', 'name')),
            field_data=DictFieldData({}),
        )

    def test_get_context(self):
        """"test get_context"""
        rendered_context = self.descriptor.get_context()
        self.assertListEqual(rendered_context['tabs'], self.tabs)
