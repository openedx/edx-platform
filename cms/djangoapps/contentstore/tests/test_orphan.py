"""
Test finding orphans via the view and django config
"""
import json
from contentstore.tests.utils import CourseTestCase
from student.models import CourseEnrollment
from contentstore.utils import reverse_course_url


class TestOrphanBase(CourseTestCase):
    """
    Base class for Studio tests that require orphaned modules
    """
    def setUp(self):
        super(TestOrphanBase, self).setUp()

        # create chapters and add them to course tree
        chapter1 = self.store.create_child(self.user.id, self.course.location, 'chapter', "Chapter1")
        self.store.publish(chapter1.location, self.user.id)

        chapter2 = self.store.create_child(self.user.id, self.course.location, 'chapter', "Chapter2")
        self.store.publish(chapter2.location, self.user.id)

        # orphan chapter
        orphan_chapter = self.store.create_item(self.user.id, self.course.id, 'chapter', "OrphanChapter")
        self.store.publish(orphan_chapter.location, self.user.id)

        # create vertical and add it as child to chapter1
        vertical1 = self.store.create_child(self.user.id, chapter1.location, 'vertical', "Vertical1")
        self.store.publish(vertical1.location, self.user.id)

        # create orphan vertical
        orphan_vertical = self.store.create_item(self.user.id, self.course.id, 'vertical', "OrphanVert")
        self.store.publish(orphan_vertical.location, self.user.id)

        # create component and add it to vertical1
        html1 = self.store.create_child(self.user.id, vertical1.location, 'html', "Html1")
        self.store.publish(html1.location, self.user.id)

        # create component and add it as a child to vertical1 and orphan_vertical
        multi_parent_html = self.store.create_child(self.user.id, vertical1.location, 'html', "multi_parent_html")
        self.store.publish(multi_parent_html.location, self.user.id)

        orphan_vertical.children.append(multi_parent_html.location)
        self.store.update_item(orphan_vertical, self.user.id)

        # create an orphaned html module
        orphan_html = self.store.create_item(self.user.id, self.course.id, 'html', "OrphanHtml")
        self.store.publish(orphan_html.location, self.user.id)

        self.store.create_child(self.user.id, self.course.location, 'static_tab', "staticuno")
        self.store.create_child(self.user.id, self.course.location, 'about', "overview")
        self.store.create_child(self.user.id, self.course.location, 'course_info', "updates")


class TestOrphan(TestOrphanBase):
    """
    Test finding orphans via view and django config
    """
    def setUp(self):
        super(TestOrphan, self).setUp()
        self.orphan_url = reverse_course_url('orphan_handler', self.course.id)

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

        # make sure that any children with one orphan parent and one non-orphan
        # parent are not deleted
        self.assertTrue(self.store.has_item(self.course.id.make_usage_key('html', "multi_parent_html")))

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
