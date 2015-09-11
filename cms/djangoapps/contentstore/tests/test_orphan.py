"""
Test finding orphans via the view and django config
"""
import json
from contentstore.tests.utils import CourseTestCase
from student.models import CourseEnrollment
from contentstore.utils import reverse_course_url
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.split_mongo import BlockKey
import ddt


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


    def course_orphans_one_branch(self, branch=None, DOC=None):
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        chapter = ItemFactory.create(category='chapter', parent=course)
        sequential = ItemFactory.create(category='sequential', parent=chapter)
        vertical = ItemFactory.create(category='vertical', parent=sequential)
        html = ItemFactory.create(category='html', parent=vertical)

        return course

    def course_with_orphans_in_branch(self, branch, DOC):
        """
        Tests that if there are orphans only on the published branch,
        running delete orphans with a course key that specifies
        the published branch will delete the published orphan

        branch is a BranchName (like draft-branch or published-branch)
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        # create an orphan
        category = 'chapter' if DOC else 'html'
        orphan = self.store.create_item(self.user.id, course.id, category, "OrphanHtml")
        self.store.publish(orphan.location, self.user.id)

        # grab the branch of the course we want to make the orphan on
        published_branch = course.id.for_branch(
            branch
        )

        # assert that this orphan is present in both branches
        self.assertOrphanCount(course.id, 1)
        self.assertOrphanCount(published_branch, 1)

        # Delete the orphan from the other branch without
        # auto-publishing the change to the this draft.
        # Now, the orphan will only be on this branch
        revision = None
        if branch == ModuleStoreEnum.BranchName.draft:
            revision = ModuleStoreEnum.RevisionOption.published_only

        self.store.delete_item(
            orphan.location,
            self.user.id,
            revision=revision,
            skip_auto_publish=True,
        )
        return course

    def assertOrphanCount(self, course_key, number):
        self.assertEqual(len(self.store.get_orphans(course_key)), number)


@ddt.ddt
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


    @ddt.data(
        ('published-branch', 0, 1, True),
        ('published-branch', 0, 1, False),
        ('draft-branch', 1, 0, True),
        ('draft-branch', 1, 0, False)
    )
    @ddt.unpack
    def test_split_mongo_orphan_delete(self, branch, draft_orphans, published_orphans, DOC):
        course = self.course_with_orphans_in_branch(branch, DOC)
        store = self.store._get_modulestore_by_type('split')

        self.assertOrphanCount(course.id, draft_orphans)
        self.assertOrphanCount(course.id.for_branch('published-branch'), published_orphans)

        store.delete_orphans(course.id, self.user.id)

        self.assertOrphanCount(course.id, 0)
        self.assertOrphanCount(course.id.for_branch('published-branch'), 0)


    def test_split_mongo_orphan_delete_2(self):
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        chapter = ItemFactory.create(category='chapter', parent=course)
        sequential = ItemFactory.create(category='sequential', parent=chapter)
        vertical = ItemFactory.create(category='vertical', parent=sequential)
        html = ItemFactory.create(category='html', parent=vertical)

        pub = course.id.for_branch('published-branch')
        course_id = course.id
        store = self.store._get_modulestore_by_type('split')

        chapter_key = BlockKey.from_usage_key(chapter.location)

        original_structure = store._lookup_course(pub).structure

        new_structure = store.version_structure(pub, original_structure, self.user.id)

        new_structure['blocks'][chapter_key].fields['children'] = []
        parent_block_keys = store._get_parents_from_structure(chapter.location, original_structure)
        parent_block_key = parent_block_key
        store.decache_block(chapter.location.course_key, new_id, parent_block_key)

        index_entry = store._get_index_if_valid(course.id)
        new_id = new_structure['_id']

        # update index if appropriate and structures
        store.update_structure(usage_locator.course_key, new_structure)

        if index_entry is not None:
            # update the index entry if appropriate
            store._update_head(course.id, index_entry, 'published-branch', new_id)
            result = usage_locator.course_key.for_version(new_id)
        else:
            result = CourseLocator(version_guid=new_id)




        # import ipdb; ipdb.set_trace()



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
