"""
Test for the OLX REST API app.
"""
import re
from xml.dom import minidom

from openedx.core.djangolib.testing.utils import skip_unless_cms
from common.djangoapps.student.roles import CourseStaffRole
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import ToyCourseFactory


@skip_unless_cms
class OlxRestApiTestCase(SharedModuleStoreTestCase):
    """
    Test the views (and consequently all the other code) of the OLX REST API.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up a course for use in these tests
        """
        super().setUpClass()
        with cls.store.default_store(ModuleStoreEnum.Type.split):
            cls.course = ToyCourseFactory.create(modulestore=cls.store)
        assert str(cls.course.id).startswith("course-v1:"), "This test is for split mongo course exports only"
        cls.unit_key = cls.course.id.make_usage_key('vertical', 'vertical_test')

    def setUp(self):
        """
        Per-test setup
        """
        super().setUp()
        self.user = UserFactory.create(password='edx')
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id)
        self.client.login(username=self.user.username, password='edx')

    # Helper methods:

    def assertXmlEqual(self, xml_str_a, xml_str_b):
        """
        Assert that the given XML strings are equal,
        ignoring attribute order and some whitespace variations.
        """
        def clean(xml_str):
            # Collapse repeated whitespace:
            xml_str = re.sub(r'(\s)\s+', r'\1', xml_str)
            xml_bytes = xml_str.encode('utf8')
            return minidom.parseString(xml_bytes).toprettyxml()
        self.assertEqual(clean(xml_str_a), clean(xml_str_b))

    def get_olx_response_for_block(self, block_id):
        return self.client.get('/api/olx-export/v1/xblock/{}/'.format(block_id))

    # Actual tests:

    def test_no_permission(self):
        """
        A regular user enrolled in the course (but not part of the authoring
        team) should not be able to use the API.
        """
        response = self.get_olx_response_for_block(self.unit_key)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()['detail'],
            'You must be a member of the course team in Studio to export OLX using this API.'
        )

    def test_export(self):
        """
        A staff user should be able to use this API to get the OLX of XBlocks in
        the course.
        """
        CourseStaffRole(self.course.id).add_users(self.user)

        response = self.get_olx_response_for_block(self.unit_key)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['root_block_id'],
            str(self.unit_key),
        )
        blocks = response.json()['blocks']
        # Check the OLX of the root block:
        self.assertXmlEqual(
            blocks[str(self.unit_key)]['olx'],
            '<unit>\n'
            '  <xblock-include definition="video/sample_video"/>\n'
            '  <xblock-include definition="video/separate_file_video"/>\n'
            '  <xblock-include definition="video/video_with_end_time"/>\n'
            '  <xblock-include definition="poll_question/T1_changemind_poll_foo_2"/>\n'
            '</unit>\n'
        )
        # Check the OLX of a video
        self.assertXmlEqual(
            blocks[str(self.course.id.make_usage_key('video', 'sample_video'))]['olx'],
            '<video youtube="0.75:JMD_ifUUfsU,1.00:OEoXaMPEzfM,1.25:AKqURZnYqpk,1.50:DYpADpL7jAY" '
            'display_name="default" youtube_id_0_75="JMD_ifUUfsU" youtube_id_1_0="OEoXaMPEzfM" '
            'youtube_id_1_25="AKqURZnYqpk" youtube_id_1_5="DYpADpL7jAY"/>\n'
        )

    def test_html_with_static_asset(self):
        """
        Test that HTML gets converted to use CDATA and static assets are
        handled.
        """
        CourseStaffRole(self.course.id).add_users(self.user)

        block_id = str(self.course.id.make_usage_key('html', 'just_img'))
        response = self.get_olx_response_for_block(block_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['root_block_id'], block_id)
        block_data = response.json()['blocks'][block_id]
        self.assertXmlEqual(
            block_data['olx'],
            '''
            <html display_name="Text"><![CDATA[
                <img src="/static/foo_bar.jpg" />
            ]]></html>
            '''
        )
        self.assertIn('static_files', block_data)
        self.assertIn('foo_bar.jpg', block_data['static_files'])
        url = block_data['static_files']['foo_bar.jpg']['url']
        self.assertEqual(url, 'http://testserver/asset-v1:edX+toy+2012_Fall+type@asset+block@foo_bar.jpg')
