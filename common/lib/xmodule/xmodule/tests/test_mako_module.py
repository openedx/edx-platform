""" Test mako_module.py """

from unittest import TestCase
from mock import Mock
from nose.plugins.attrib import attr

from xmodule.mako_module import MakoModuleDescriptor


@attr(shard=1)
class MakoModuleTest(TestCase):
    """ Test MakoModuleDescriptor """

    def test_render_template_check(self):
        mock_system = Mock()
        mock_system.render_template = None

        with self.assertRaises(TypeError):
            MakoModuleDescriptor(mock_system, {})

        del mock_system.render_template

        with self.assertRaises(TypeError):
            MakoModuleDescriptor(mock_system, {})
