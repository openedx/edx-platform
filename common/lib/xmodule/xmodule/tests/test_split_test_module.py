"""
Tests for the Split Testing Module
"""
import ddt
import lxml
from mock import Mock, patch
from fs.memoryfs import MemoryFS

from xmodule.tests.xml import factories as xml
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests import get_test_system
from xmodule.split_test_module import SplitTestDescriptor, SplitTestFields, ValidationMessageType
from xmodule.partitions.partitions import Group, UserPartition
from xmodule.partitions.test_partitions import StaticPartitionService, MemoryUserTagsService


class SplitTestModuleFactory(xml.XmlImportFactory):
    """
    Factory for generating SplitTestModules for testing purposes
    """
    tag = 'split_test'


class SplitTestModuleTest(XModuleXmlImportTest):
    """
    Base class for all split_module tests.
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
        xml.HtmlFactory(parent=split_test, url_name='split_test_cond0', text='HTML FOR GROUP 0')
        xml.HtmlFactory(parent=split_test, url_name='split_test_cond1', text='HTML FOR GROUP 1')

        self.course = self.process_xml(course)
        self.course_sequence = self.course.get_children()[0]
        self.module_system = get_test_system()

        def get_module(descriptor):
            """Mocks module_system get_module function"""
            module_system = get_test_system()
            module_system.get_module = get_module
            descriptor.bind_for_student(module_system, descriptor._field_data)  # pylint: disable=protected-access
            return descriptor

        self.module_system.get_module = get_module
        self.module_system.descriptor_system = self.course.runtime
        self.course.runtime.export_fs = MemoryFS()

        self.tags_service = MemoryUserTagsService()
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

        self.split_test_module = self.course_sequence.get_children()[0]
        self.split_test_module.bind_for_student(self.module_system, self.split_test_module._field_data)  # pylint: disable=protected-access


@ddt.ddt
class SplitTestModuleLMSTest(SplitTestModuleTest):
    """
    Test the split test module
    """

    @ddt.data(('0', 'split_test_cond0'), ('1', 'split_test_cond1'))
    @ddt.unpack
    def test_child(self, user_tag, child_url_name):
        self.tags_service.set_tag(
            self.tags_service.COURSE_SCOPE,
            'xblock.partition_service.partition_0',
            user_tag
        )

        self.assertEquals(self.split_test_module.child_descriptor.url_name, child_url_name)

    @ddt.data(('0',), ('1',))
    @ddt.unpack
    def test_child_old_tag_value(self, _user_tag):
        # If user_tag has a stale value, we should still get back a valid child url
        self.tags_service.set_tag(
            self.tags_service.COURSE_SCOPE,
            'xblock.partition_service.partition_0',
            '2'
        )

        self.assertIn(self.split_test_module.child_descriptor.url_name, ['split_test_cond0', 'split_test_cond1'])

    @ddt.data(('0', 'HTML FOR GROUP 0'), ('1', 'HTML FOR GROUP 1'))
    @ddt.unpack
    def test_get_html(self, user_tag, child_content):
        self.tags_service.set_tag(
            self.tags_service.COURSE_SCOPE,
            'xblock.partition_service.partition_0',
            user_tag
        )

        self.assertIn(
            child_content,
            self.module_system.render(self.split_test_module, 'student_view').content
        )

    @ddt.data(('0',), ('1',))
    @ddt.unpack
    def test_child_missing_tag_value(self, _user_tag):
        # If user_tag has a missing value, we should still get back a valid child url
        self.assertIn(self.split_test_module.child_descriptor.url_name, ['split_test_cond0', 'split_test_cond1'])

    @ddt.data(('100',), ('200',), ('300',), ('400',), ('500',), ('600',), ('700',), ('800',), ('900',), ('1000',))
    @ddt.unpack
    def test_child_persist_new_tag_value_when_tag_missing(self, _user_tag):
        # If a user_tag has a missing value, a group should be saved/persisted for that user.
        # So, we check that we get the same url_name when we call on the url_name twice.
        # We run the test ten times so that, if our storage is failing, we'll be most likely to notice it.
        self.assertEquals(self.split_test_module.child_descriptor.url_name, self.split_test_module.child_descriptor.url_name)

    # Patch the definition_to_xml for the html children.
    @patch('xmodule.html_module.HtmlDescriptor.definition_to_xml')
    def test_export_import_round_trip(self, def_to_xml):
        # The HtmlDescriptor definition_to_xml tries to write to the filesystem
        # before returning an xml object. Patch this to just return the xml.
        def_to_xml.return_value = lxml.etree.Element('html')

        # Mock out the process_xml
        # Expect it to return a child descriptor for the SplitTestDescriptor when called.
        self.module_system.process_xml = Mock()

        # Write out the xml.
        xml_obj = self.split_test_module.definition_to_xml(MemoryFS())

        self.assertEquals(xml_obj.get('user_partition_id'), '0')
        self.assertIsNotNone(xml_obj.get('group_id_to_child'))

        # Read the xml back in.
        fields, children = SplitTestDescriptor.definition_from_xml(xml_obj, self.module_system)
        self.assertEquals(fields.get('user_partition_id'), '0')
        self.assertIsNotNone(fields.get('group_id_to_child'))
        self.assertEquals(len(children), 2)


class SplitTestModuleStudioTest(SplitTestModuleTest):
    """
    Unit tests for how split test interacts with Studio.
    """

    def test_render_studio_view(self):
        """
        Test the rendering of the Studio view.
        """

        # The split_test module should render both its groups when it is the root
        reorderable_items = set()
        context = {
            'runtime_type': 'studio',
            'container_view': True,
            'reorderable_items': reorderable_items,
            'root_xblock': self.split_test_module,
        }
        html = self.module_system.render(self.split_test_module, 'student_view', context).content
        self.assertIn('HTML FOR GROUP 0', html)
        self.assertIn('HTML FOR GROUP 1', html)

        # When rendering as a child, it shouldn't render either of its groups
        reorderable_items = set()
        context = {
            'runtime_type': 'studio',
            'container_view': True,
            'reorderable_items': reorderable_items,
            'root_xblock': self.course_sequence,
        }
        html = self.module_system.render(self.split_test_module, 'student_view', context).content
        self.assertNotIn('HTML FOR GROUP 0', html)
        self.assertNotIn('HTML FOR GROUP 1', html)

    def test_editable_settings(self):
        """
        Test the setting information passed back from editable_metadata_fields.
        """
        editable_metadata_fields = self.split_test_module.editable_metadata_fields
        self.assertIn(SplitTestDescriptor.display_name.name, editable_metadata_fields)
        self.assertNotIn(SplitTestDescriptor.due.name, editable_metadata_fields)
        self.assertNotIn(SplitTestDescriptor.user_partitions.name, editable_metadata_fields)

        # user_partition_id will only appear in the editable settings if the value is the
        # default "unselected" value. This split instance has user_partition_id = 0, so
        # user_partition_id will not be editable.
        self.assertNotIn(SplitTestDescriptor.user_partition_id.name, editable_metadata_fields)

        # Explicitly set user_partition_id to the default value. Now user_partition_id will be editable.
        self.split_test_module.user_partition_id = SplitTestFields.no_partition_selected['value']
        editable_metadata_fields = self.split_test_module.editable_metadata_fields
        self.assertIn(SplitTestDescriptor.user_partition_id.name, editable_metadata_fields)

    def test_non_editable_settings(self):
        """
        Test the settings that are marked as "non-editable".
        """
        non_editable_metadata_fields = self.split_test_module.non_editable_metadata_fields
        self.assertIn(SplitTestDescriptor.due, non_editable_metadata_fields)
        self.assertIn(SplitTestDescriptor.user_partitions, non_editable_metadata_fields)
        self.assertNotIn(SplitTestDescriptor.display_name, non_editable_metadata_fields)

    def test_available_partitions(self):
        """
        Tests that the available partitions are populated correctly when editable_metadata_fields are called
        """
        self.assertEqual([], SplitTestDescriptor.user_partition_id.values)

        # user_partitions is empty, only the "Not Selected" item will appear.
        self.split_test_module.editable_metadata_fields  # pylint: disable=pointless-statement
        partitions = SplitTestDescriptor.user_partition_id.values
        self.assertEqual(1, len(partitions))
        self.assertEqual(SplitTestFields.no_partition_selected['value'], partitions[0]['value'])

        # Populate user_partitions and call editable_metadata_fields again
        self.split_test_module.user_partitions = [
            UserPartition(0, 'first_partition', 'First Partition', [Group("0", 'alpha'), Group("1", 'beta')])
        ]
        self.split_test_module.editable_metadata_fields  # pylint: disable=pointless-statement
        self.assertEqual(2, len(partitions))
        self.assertEqual(SplitTestFields.no_partition_selected['value'], partitions[0]['value'])
        self.assertEqual(0, partitions[1]['value'])
        self.assertEqual("first_partition", partitions[1]['display_name'])

    def test_validation_messages(self):
        """
        Test the validation messages produced for different split_test configurations.
        """

        def verify_validation_message(split_test_module, expected_message, expected_message_type):
            (message, message_type) = split_test_module.validation_message()
            self.assertEqual(message, expected_message)
            self.assertEqual(message_type, expected_message_type)

        # Verify the message for an unconfigured experiment
        self.split_test_module.user_partition_id = -1
        verify_validation_message(self.split_test_module,
                                  u"This content experiment needs to be assigned to a group configuration.",
                                  ValidationMessageType.warning)

        # Verify the message for a correctly configured experiment
        self.split_test_module.user_partition_id = 0
        self.split_test_module.user_partitions = [
            UserPartition(0, 'first_partition', 'First Partition', [Group("0", 'alpha'), Group("1", 'beta')])
        ]
        verify_validation_message(self.split_test_module,
                                  u"This content experiment is part of group configuration 'first_partition'.",
                                  ValidationMessageType.information)

        # Verify the message for a block with the wrong number of groups
        self.split_test_module.user_partitions = [
            UserPartition(0, 'first_partition', 'First Partition',
                          [Group("0", 'alpha'), Group("1", 'beta'), Group("2", 'gamma')])
        ]
        verify_validation_message(self.split_test_module,
                                  u"This content experiment is in an invalid state and cannot be repaired. "
                                  u"Please delete and recreate.",
                                  ValidationMessageType.error)

        # Verify the message for a block referring to a non-existent experiment
        self.split_test_module.user_partition_id = 2
        verify_validation_message(self.split_test_module,
                                  u"This content experiment will not be shown to students because it refers "
                                  u"to a group configuration that has been deleted. "
                                  u"You can delete this experiment or reinstate the group configuration to repair it.",
                                  ValidationMessageType.error)
