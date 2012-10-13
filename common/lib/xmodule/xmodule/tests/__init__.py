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

import capa.calc as calc
import xmodule
from xmodule.x_module import ModuleSystem
from mock import Mock

i4xs = ModuleSystem(
    ajax_url='courses/course_id/modx/a_location',
    track_function=Mock(),
    get_module=Mock(),
    render_template=Mock(),
    replace_urls=Mock(),
    user=Mock(),
    filestore=Mock(),
    debug=True,
    xqueue={'interface':None, 'callback_url':'/', 'default_queuename': 'testqueue', 'waittime': 10},
    node_path=os.environ.get("NODE_PATH", "/usr/local/lib/node_modules"),
    anonymous_student_id = 'student'
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
        self.assertTrue(abs(calc.evaluator(variables, functions, "t") - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T") - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "t", cs=True) - 1.0) < 0.00001)
        self.assertTrue(abs(calc.evaluator(variables, functions, "T", cs=True) - 298) < 0.2)
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

