"""
Test finding orphans via the view and django config
"""
import json
from contentstore.tests.utils import CourseTestCase
from student.models import CourseEnrollment
from xmodule.modulestore.django import modulestore
from contentstore.utils import reverse_course_url


class TestOrphan(CourseTestCase):
    """
    Test finding orphans via view and django config
    """
    def setUp(self):
        super(TestOrphan, self).setUp()

        runtime = self.course.runtime

        self._create_item('chapter', 'Chapter1', {}, {'display_name': 'Chapter 1'}, 'course', self.course.location.name, runtime)
        self._create_item('chapter', 'Chapter2', {}, {'display_name': 'Chapter 2'}, 'course', self.course.location.name, runtime)
        self._create_item('chapter', 'OrphanChapter', {}, {'display_name': 'Orphan Chapter'}, None, None, runtime)
        self._create_item('vertical', 'Vert1', {}, {'display_name': 'Vertical 1'}, 'chapter', 'Chapter1', runtime)
        self._create_item('vertical', 'OrphanVert', {}, {'display_name': 'Orphan Vertical'}, None, None, runtime)
        self._create_item('html', 'Html1', "<p>Goodbye</p>", {'display_name': 'Parented Html'}, 'vertical', 'Vert1', runtime)
        self._create_item('html', 'OrphanHtml', "<p>Hello</p>", {'display_name': 'Orphan html'}, None, None, runtime)
        self._create_item('static_tab', 'staticuno', "<p>tab</p>", {'display_name': 'Tab uno'}, None, None, runtime)
        self._create_item('about', 'overview', "<p>overview</p>", {}, None, None, runtime)
        self._create_item('course_info', 'updates', "<ol><li><h2>Sep 22</h2><p>test</p></li></ol>", {}, None, None, runtime)

        self.orphan_url = reverse_course_url('orphan_handler', self.course.id)

    def _create_item(self, category, name, data, metadata, parent_category, parent_name, runtime):
        location = self.course.location.replace(category=category, name=name)
        store = modulestore()
        store.create_item(
            self.user.id,
            location.course_key,
            location.block_type,
            location.block_id,
            definition_data=data,
            metadata=metadata,
            runtime=runtime
        )
        if parent_name:
            # add child to parent in mongo
            parent_location = self.course.location.replace(category=parent_category, name=parent_name)
            parent = store.get_item(parent_location)
            parent.children.append(location)
            store.update_item(parent, self.user.id)

    def test_mongo_orphan(self):
        """
        Test that old mongo finds the orphans
        """
        orphans = json.loads(
            self.client.get(
                self.orphan_url,
                HTTP_ACCEPT='application/json'
            ).content
        )
        self.assertEqual(len(orphans), 3, "Wrong # {}".format(orphans))
        location = self.course.location.replace(category='chapter', name='OrphanChapter')
        self.assertIn(location.to_deprecated_string(), orphans)
        location = self.course.location.replace(category='vertical', name='OrphanVert')
        self.assertIn(location.to_deprecated_string(), orphans)
        location = self.course.location.replace(category='html', name='OrphanHtml')
        self.assertIn(location.to_deprecated_string(), orphans)

    def test_mongo_orphan_delete(self):
        """
        Test that old mongo deletes the orphans
        """
        self.client.delete(self.orphan_url)
        orphans = json.loads(
            self.client.get(self.orphan_url, HTTP_ACCEPT='application/json').content
        )
        self.assertEqual(len(orphans), 0, "Orphans not deleted {}".format(orphans))

    def test_not_permitted(self):
        """
        Test that auth restricts get and delete appropriately
        """
        test_user_client, test_user = self.create_non_staff_authed_user_client()
        CourseEnrollment.enroll(test_user, self.course.id)
        response = test_user_client.get(self.orphan_url)
        self.assertEqual(response.status_code, 403)
        response = test_user_client.delete(self.orphan_url)
        self.assertEqual(response.status_code, 403)
