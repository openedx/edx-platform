import unittest
import courseware.modules

class ModelsTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_module_class(self):
        vc = courseware.modules.get_module_class('video')
        vc_str = "<class 'courseware.modules.video_module.Module'>"
        self.assertEqual(str(vc), vc_str)

