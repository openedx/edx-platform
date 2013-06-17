# -*- coding: utf-8 -*-
import unittest

from xmodule.video_module import VideoDescriptor
from .test_import import DummySystem


class VideoDescriptorImportTestCase(unittest.TestCase):
    """
    Make sure that VideoDescriptor can import an old XML-based video correctly.
    """

    def test_from_xml(self):
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                   show_captions="false"
                   from="00:00:01"
                   to="00:01:00">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </video>
        '''
        output = VideoDescriptor.from_xml(xml_data, module_system)
        self.assertEquals(output.youtube_id_0_75, 'izygArpw-Qo')
        self.assertEquals(output.youtube_id_1_0, 'p2Q6BrNhdh8')
        self.assertEquals(output.youtube_id_1_25, '1EeWXzPdhSA')
        self.assertEquals(output.youtube_id_1_5, 'rABDYkeK0x8')
        self.assertEquals(output.show_captions, False)
        self.assertEquals(output.start_time, 1.0)
        self.assertEquals(output.end_time, 60)
        self.assertEquals(output.track, 'http://www.example.com/track')
        self.assertEquals(output.source, 'http://www.example.com/source.mp4')

    def test_from_xml_missing_attributes(self):
        """
        Ensure that attributes have the right values if they aren't
        explicitly set in XML.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '''
            <video display_name="Test Video"
                   youtube="1.0:p2Q6BrNhdh8,1.25:1EeWXzPdhSA"
                   show_captions="true">
              <source src="http://www.example.com/source.mp4"/>
              <track src="http://www.example.com/track"/>
            </video>
        '''
        output = VideoDescriptor.from_xml(xml_data, module_system)
        self.assertEquals(output.youtube_id_0_75, '')
        self.assertEquals(output.youtube_id_1_0, 'p2Q6BrNhdh8')
        self.assertEquals(output.youtube_id_1_25, '1EeWXzPdhSA')
        self.assertEquals(output.youtube_id_1_5, '')
        self.assertEquals(output.show_captions, True)
        self.assertEquals(output.start_time, 0.0)
        self.assertEquals(output.end_time, 0.0)
        self.assertEquals(output.track, 'http://www.example.com/track')
        self.assertEquals(output.source, 'http://www.example.com/source.mp4')

    def test_from_xml_no_attributes(self):
        """
        Make sure settings are correct if none are explicitly set in XML.
        """
        module_system = DummySystem(load_error_modules=True)
        xml_data = '<video></video>'
        output = VideoDescriptor.from_xml(xml_data, module_system)
        self.assertEquals(output.youtube_id_0_75, '')
        self.assertEquals(output.youtube_id_1_0, 'OEoXaMPEzfM')
        self.assertEquals(output.youtube_id_1_25, '')
        self.assertEquals(output.youtube_id_1_5, '')
        self.assertEquals(output.show_captions, True)
        self.assertEquals(output.start_time, 0.0)
        self.assertEquals(output.end_time, 0.0)
        self.assertEquals(output.track, '')
        self.assertEquals(output.source, '')
