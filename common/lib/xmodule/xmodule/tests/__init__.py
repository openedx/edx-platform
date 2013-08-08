"""
unittests for xmodule

Run like this:

    rake test_common/lib/xmodule

"""

import unittest
import os
import fs
import fs.osfs

import numpy

import json

import calc
import xmodule
from xmodule.x_module import ModuleSystem
from mock import Mock


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
        vc = xmodule.x_module.XModuleDescriptor.load_class('video')
        vc_str = "<class 'xmodule.video_module.VideoDescriptor'>"
        self.assertEqual(str(vc), vc_str)

    def test_calc(self):
        variables = {'R1': 2.0, 'R3': 4.0}
        functions = {'sin': numpy.sin, 'cos': numpy.cos}

        self.assertTrue(abs(calc.evaluator(variables, functions, "10000||sin(7+5)+0.5356")) < 0.01)
        self.assertEqual(calc.evaluator({'R1': 2.0, 'R3': 4.0}, {}, "13"), 13)
        self.assertEqual(calc.evaluator(variables, functions, "13"), 13)
        self.assertEqual(calc.evaluator({'a': 2.2997471478310274, 'k': 9, 'm': 8, 'x': 0.66009498411213041}, {}, "5"), 5)
        self.assertEqual(calc.evaluator({}, {}, "-1"), -1)
        self.assertEqual(calc.evaluator({}, {}, "-0.33"), -.33)
        self.assertEqual(calc.evaluator({}, {}, "-.33"), -.33)
        self.assertEqual(calc.evaluator(variables, functions, "R1*R3"), 8.0)
        self.assertTrue(abs(calc.evaluator(variables, functions, "sin(e)-0.41")) < 0.01)
        self.assertTrue(abs(calc.evaluator(variables, functions, "k*T/q-0.025")) < 0.001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "e^(j*pi)") + 1) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "j||1") - 0.5 - 0.5j) < 0.00001)
        variables['t'] = 1.0
        # Use self.assertAlmostEqual here...
        self.assertTrue(abs(calc.evaluator(variables, functions, "t") - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T") - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "t", cs=True) - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T", cs=True) - 298) < 0.2)
        # Use self.assertRaises here...
        exception_happened = False
        try:
            calc.evaluator({}, {}, "5+7 QWSEKO")
        except:
            exception_happened = True
        self.assertTrue(exception_happened)

        try:
            calc.evaluator({'r1': 5}, {}, "r1+r2")
        except calc.UndefinedVariable:
            pass

        self.assertEqual(calc.evaluator(variables, functions, "r1*r3"), 8.0)

        exception_happened = False
        try:
            calc.evaluator(variables, functions, "r1*r3", cs=True)
        except:
            exception_happened = True
        self.assertTrue(exception_happened)


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
