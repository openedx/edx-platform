"""
unittests for xmodule

Run like this:

    rake test_common/lib/xmodule

"""

import json
import os
import pprint
import unittest

from mock import Mock
from path import path

from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xmodule.x_module import ModuleSystem, XModuleDescriptor, XModuleMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.locations import SlashSeparatedCourseKey
from xmodule.mako_module import MakoDescriptorSystem
from xmodule.error_module import ErrorDescriptor


MODULE_DIR = path(__file__).dirname()
# Location of common test DATA directory
# '../../../../edx-platform/common/test/data/'
DATA_DIR = MODULE_DIR.parent.parent.parent.parent / "test" / "data"


open_ended_grading_interface = {
    'url': 'blah/',
    'username': 'incorrect_user',
    'password': 'incorrect_pass',
    'staff_grading': 'staff_grading',
    'peer_grading': 'peer_grading',
    'grading_controller': 'grading_controller',
}


class TestModuleSystem(ModuleSystem):  # pylint: disable=abstract-method
    """
    ModuleSystem for testing
    """
    def handler_url(self, block, handler, suffix='', query='', thirdparty=False):
        return '{usage_id}/{handler}{suffix}?{query}'.format(
            usage_id=block.scope_ids.usage_id.to_deprecated_string(),
            handler=handler,
            suffix=suffix,
            query=query,
        )

    def local_resource_url(self, block, uri):
        return 'resource/{usage_id}/{uri}'.format(
            usage_id=block.scope_ids.usage_id.to_deprecated_string(),
            uri=uri,
        )


def get_test_system(course_id=SlashSeparatedCourseKey('org', 'course', 'run')):
    """
    Construct a test ModuleSystem instance.

    By default, the render_template() method simply returns the repr of the
    context it is passed.  You can override this behavior by monkey patching::

        system = get_test_system()
        system.render_template = my_render_func

    where `my_render_func` is a function of the form my_render_func(template, context).

    """
    return TestModuleSystem(
        static_url='/static',
        track_function=Mock(),
        get_module=Mock(),
        render_template=mock_render_template,
        replace_urls=str,
        user=Mock(is_staff=False),
        filestore=Mock(),
        debug=True,
        hostname="edx.org",
        xqueue={'interface': None, 'callback_url': '/', 'default_queuename': 'testqueue', 'waittime': 10, 'construct_callback' : Mock(side_effect="/")},
        node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
        anonymous_student_id='student',
        open_ended_grading_interface=open_ended_grading_interface,
        course_id=course_id,
        error_descriptor_class=ErrorDescriptor,
        get_user_role=Mock(is_staff=False),
        descriptor_runtime=get_test_descriptor_system(),
    )


def get_test_descriptor_system():
    """
    Construct a test DescriptorSystem instance.
    """
    return MakoDescriptorSystem(
        load_item=Mock(),
        resources_fs=Mock(),
        error_tracker=Mock(),
        render_template=mock_render_template,
        mixins=(InheritanceMixin, XModuleMixin),
        field_data=DictFieldData({}),
    )


def mock_render_template(*args, **kwargs):
    """
    Pretty-print the args and kwargs.

    Allows us to not depend on any actual template rendering mechanism,
    while still returning a unicode object
    """
    return pprint.pformat((args, kwargs)).decode()


class ModelsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_class(self):
        vc = XModuleDescriptor.load_class('video')
        vc_str = "<class 'xmodule.video_module.video_module.VideoDescriptor'>"
        self.assertEqual(str(vc), vc_str)


class LogicTest(unittest.TestCase):
    """Base class for testing xmodule logic."""
    descriptor_class = None
    raw_field_data = {}

    def setUp(self):
        class EmptyClass:
            """Empty object."""
            url_name = ''
            category = 'test'

        self.system = get_test_system()
        self.descriptor = EmptyClass()

        self.xmodule_class = self.descriptor_class.module_class
        usage_key = self.system.course_id.make_usage_key(self.descriptor.category, 'test_loc')
        # ScopeIds has 4 fields: user_id, block_type, def_id, usage_id
        scope_ids = ScopeIds(1, self.descriptor.category, usage_key, usage_key)
        self.xmodule = self.xmodule_class(
            self.descriptor, self.system, DictFieldData(self.raw_field_data), scope_ids
        )

    def ajax_request(self, dispatch, data):
        """Call Xmodule.handle_ajax."""
        return json.loads(self.xmodule.handle_ajax(dispatch, data))
