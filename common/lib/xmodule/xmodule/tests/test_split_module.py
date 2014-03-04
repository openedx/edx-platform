"""
Tests for the Split Testing Module
"""
import ddt
from mock import Mock

from xmodule.tests.xml import factories as xml
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests import get_test_system
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.partitions.test_partitions import StaticPartitionService


class SplitTestModuleFactory(xml.XmlImportFactory):
    """
    Factory for generating SplitTestModules for testing purposes
    """
    tag = 'split_test'


@ddt.ddt
class SplitTestModuleTest(XModuleXmlImportTest):
    """
    Test the split test module
    """

    def setUp(self):
        self.course_id = 'test_org/test_course_number/test_run'
        # construct module
        course = xml.CourseFactory.build()
        sequence = xml.SequenceFactory.build(parent=course)
        split_test = SplitTestModuleFactory(
            parent=sequence,
            attribs={
                'user_partition_id': '0',
                'group_id_to_child': '{"0": "i4x://edX/xml_test_course/html/split_test_cond0", "1": "i4x://edX/xml_test_course/html/split_test_cond1"}'
            }
        )
        xml.HtmlFactory(parent=split_test, url_name='split_test_cond0')
        xml.HtmlFactory(parent=split_test, url_name='split_test_cond1')

        self.course = self.process_xml(course)
        course_seq = self.course.get_children()[0]
        self.module_system = get_test_system()

        def get_module(descriptor):
            module_system = get_test_system()
            module_system.get_module = get_module
            descriptor.bind_for_student(module_system, descriptor._field_data)
            return descriptor

        self.module_system.get_module = get_module
        self.module_system.descriptor_system = self.course.runtime

        self.tags_service = Mock(name='user_tags')
        self.module_system._services['user_tags'] = self.tags_service  # pylint: disable=protected-access

        self.partitions_service = StaticPartitionService(
            [
                UserPartition(0, 'first_partition', 'First Partition', [Group("0", 'alpha'), Group("1", 'beta')]),
                UserPartition(1, 'second_partition', 'Second Partition', [Group("0", 'abel'), Group("1", 'baker'), Group("2", 'charlie')])
            ],
            user_tags_service=self.tags_service,
            course_id=self.course.id,
            track_function=Mock(name='track_function'),
        )
        self.module_system._services['partitions'] = self.partitions_service  # pylint: disable=protected-access

        self.split_test_module = course_seq.get_children()[0]
        self.split_test_module.bind_for_student(self.module_system, self.split_test_module._field_data)


    @ddt.data(('0', 'split_test_cond0'), ('1', 'split_test_cond1'))
    @ddt.unpack
    def test_child(self, user_tag, child_url_name):
        self.tags_service.get_tag.return_value = user_tag

        self.assertEquals(self.split_test_module.child_descriptor.url_name, child_url_name)

    @ddt.data(('0', 'split_test_cond0'), ('1', 'split_test_cond1'))
    @ddt.unpack
    def test_child_old_tag_value(self, user_tag, child_url_name):  # pylint: disable=unused-argument
        # If user_tag has a stale value, we should still get back a valid child url
        self.tags_service.get_tag.return_value = '2'

        self.assertIn(self.split_test_module.child_descriptor.url_name, ['split_test_cond0', 'split_test_cond1'])

    @ddt.data(('0', 'split_test_cond0'), ('1', 'split_test_cond1'))
    @ddt.unpack
    def test_get_html(self, user_tag, child_url_name):
        self.tags_service.get_tag.return_value = user_tag
        self.module_system.render(self.split_test_module, 'student_view').content