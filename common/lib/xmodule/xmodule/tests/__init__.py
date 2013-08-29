"""
unittests for xmodule

Run like this:

    rake test_common/lib/xmodule

"""

import json
import os
import unittest

import fs
import fs.osfs
import numpy
from mock import Mock
from path import path

import calc
from xmodule.x_module import ModuleSystem, XModuleDescriptor


# Location of common test DATA directory
# '../../../../edx-platform/common/test/data/'
MODULE_DIR = path(__file__).dirname()
DATA_DIR = path.joinpath(*MODULE_DIR.splitall()[:-4]) / 'test/data/'


open_ended_grading_interface = {
        'url': 'blah/',
        'username': 'incorrect_user',
        'password': 'incorrect_pass',
        'staff_grading' : 'staff_grading',
        'peer_grading' : 'peer_grading',
        'grading_controller' : 'grading_controller'
    }


def get_test_system():
    """
    Construct a test ModuleSystem instance.

    By default, the render_template() method simply returns the repr of the
    context it is passed.  You can override this behavior by monkey patching::

        system = get_test_system()
        system.render_template = my_render_func

    where `my_render_func` is a function of the form my_render_func(template, context).

    """
    return ModuleSystem(
        ajax_url='courses/course_id/modx/a_location',
        track_function=Mock(),
        get_module=Mock(),
        render_template=lambda template, context: repr(context),
        replace_urls=lambda html: str(html),
        user=Mock(is_staff=False),
        filestore=Mock(),
        debug=True,
        xqueue={'interface': None, 'callback_url': '/', 'default_queuename': 'testqueue', 'waittime': 10, 'construct_callback' : Mock(side_effect="/")},
        node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
        xblock_model_data=lambda descriptor: descriptor._model_data,
        anonymous_student_id='student',
        open_ended_grading_interface= open_ended_grading_interface
    )


class ModelsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_class(self):
        vc = XModuleDescriptor.load_class('video')
        vc_str = "<class 'xmodule.video_module.VideoDescriptor'>"
        self.assertEqual(str(vc), vc_str)

class PostData(object):
    """Class which emulate postdata."""
    def __init__(self, dict_data):
        self.dict_data = dict_data

    def getlist(self, key):
        """Get data by key from `self.dict_data`."""
        return self.dict_data.get(key)


class LogicTest(unittest.TestCase):
    """Base class for testing xmodule logic."""
    descriptor_class = None
    raw_model_data = {}

    def setUp(self):
        class EmptyClass:
            """Empty object."""
            url_name = ''
            category = 'test'

        self.system = get_test_system()
        self.descriptor = EmptyClass()

        self.xmodule_class = self.descriptor_class.module_class
        self.xmodule = self.xmodule_class(
            self.system, self.descriptor, self.raw_model_data)

    def ajax_request(self, dispatch, data):
        """Call Xmodule.handle_ajax."""
        return json.loads(self.xmodule.handle_ajax(dispatch, data))
