import uuid
import mock
import unittest
import random
import datetime

from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.mongo import MongoModuleStore
from xmodule.modulestore.split_mongo import SplitMongoModuleStore
from xmodule.modulestore import Location
from xmodule.fields import Date
from xmodule.modulestore.locator import BlockUsageLocator, CourseLocator


class TestOrphan(unittest.TestCase):
    """
    Test the orphan finding code
    """

    # Snippet of what would be in the django settings envs file
    db_config = {
        'host': 'localhost',
        'db': 'test_xmodule',
    }

    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': '',
        'render_template': mock.Mock(return_value=""),
        'xblock_mixins': (InheritanceMixin,)
    }

    split_package_id = 'test_org.test_course.runid'

    def setUp(self):
        self.db_config['collection'] = 'modulestore{0}'.format(uuid.uuid4().hex[:5])

        self.userid = random.getrandbits(32)
        super(TestOrphan, self).setUp()
        self.split_mongo = SplitMongoModuleStore(
            self.db_config,
            **self.modulestore_options
        )
        self.addCleanup(self.tear_down_split)
        self.old_mongo = MongoModuleStore(self.db_config, **self.modulestore_options)
        self.addCleanup(self.tear_down_mongo)
        self.course_location = None
        self._create_course()

    def tear_down_split(self):
        """
        Remove the test collections, close the db connection
        """
        split_db = self.split_mongo.db
        split_db.drop_collection(split_db.course_index)
        split_db.drop_collection(split_db.structures)
        split_db.drop_collection(split_db.definitions)
        split_db.connection.close()

    def tear_down_mongo(self):
        """
        Remove the test collections, close the db connection
        """
        split_db = self.split_mongo.db
        # old_mongo doesn't give a db attr, but all of the dbs are the same
        split_db.drop_collection(self.old_mongo.collection)

    def _create_item(self, category, name, data, metadata, parent_category, parent_name, runtime):
        """
        Create the item of the given category and block id in split and old mongo, add it to the optional
        parent. The parent category is only needed because old mongo requires it for the id.
        """
        location = Location('i4x', 'test_org', 'test_course', category, name)
        self.old_mongo.create_and_save_xmodule(location, data, metadata, runtime)
        if isinstance(data, basestring):
            fields = {'data': data}
        else:
            fields = data.copy()
        fields.update(metadata)
        if parent_name:
            # add child to parent in mongo
            parent_location = Location('i4x', 'test_org', 'test_course', parent_category, parent_name)
            parent = self.old_mongo.get_item(parent_location)
            parent.children.append(location.url())
            self.old_mongo.update_item(parent, self.userid)
            # create pointer for split
            course_or_parent_locator = BlockUsageLocator(
                package_id=self.split_package_id,
                branch='draft',
                block_id=parent_name
            )
        else:
            course_or_parent_locator = CourseLocator(
                package_id='test_org.test_course.runid',
                branch='draft',
            )
        self.split_mongo.create_item(course_or_parent_locator, category, self.userid, block_id=name, fields=fields)

    def _create_course(self):
        """
        * some detached items
        * some attached children
        * some orphans
        """
        date_proxy = Date()
        metadata = {
            'start': date_proxy.to_json(datetime.datetime(2000, 3, 13, 4)),
            'display_name': 'Migration test course',
        }
        data = {
            'wiki_slug': 'test_course_slug'
        }
        fields = metadata.copy()
        fields.update(data)
        # split requires the course to be created separately from creating items
        self.split_mongo.create_course(
            self.split_package_id, 'test_org', self.userid, fields=fields, root_block_id='runid'
        )
        self.course_location = Location('i4x', 'test_org', 'test_course', 'course', 'runid')
        self.old_mongo.create_and_save_xmodule(self.course_location, data, metadata)
        runtime = self.old_mongo.get_item(self.course_location).runtime

        self._create_item('chapter', 'Chapter1', {}, {'display_name': 'Chapter 1'}, 'course', 'runid', runtime)
        self._create_item('chapter', 'Chapter2', {}, {'display_name': 'Chapter 2'}, 'course', 'runid', runtime)
        self._create_item('chapter', 'OrphanChapter', {}, {'display_name': 'Orphan Chapter'}, None, None, runtime)
        self._create_item('vertical', 'Vert1', {}, {'display_name': 'Vertical 1'}, 'chapter', 'Chapter1', runtime)
        self._create_item('vertical', 'OrphanVert', {}, {'display_name': 'Orphan Vertical'}, None, None, runtime)
        self._create_item('html', 'Html1', "<p>Goodbye</p>", {'display_name': 'Parented Html'}, 'vertical', 'Vert1', runtime)
        self._create_item('html', 'OrphanHtml', "<p>Hello</p>", {'display_name': 'Orphan html'}, None, None, runtime)
        self._create_item('static_tab', 'staticuno', "<p>tab</p>", {'display_name': 'Tab uno'}, None, None, runtime)
        self._create_item('about', 'overview', "<p>overview</p>", {}, None, None, runtime)
        self._create_item('course_info', 'updates', "<ol><li><h2>Sep 22</h2><p>test</p></li></ol>", {}, None, None, runtime)

    def test_mongo_orphan(self):
        """
        Test that old mongo finds the orphans
        """
        orphans = self.old_mongo.get_orphans(self.course_location, None)
        self.assertEqual(len(orphans), 3, "Wrong # {}".format(orphans))
        location = self.course_location.replace(category='chapter', name='OrphanChapter')
        self.assertIn(location.url(), orphans)
        location = self.course_location.replace(category='vertical', name='OrphanVert')
        self.assertIn(location.url(), orphans)
        location = self.course_location.replace(category='html', name='OrphanHtml')
        self.assertIn(location.url(), orphans)

    def test_split_orphan(self):
        """
        Test that old mongo finds the orphans
        """
        orphans = self.split_mongo.get_orphans(self.split_package_id, 'draft')
        self.assertEqual(len(orphans), 3, "Wrong # {}".format(orphans))
        location = BlockUsageLocator(package_id=self.split_package_id, branch='draft', block_id='OrphanChapter')
        self.assertIn(location, orphans)
        location = BlockUsageLocator(package_id=self.split_package_id, branch='draft', block_id='OrphanVert')
        self.assertIn(location, orphans)
        location = BlockUsageLocator(package_id=self.split_package_id, branch='draft', block_id='OrphanHtml')
        self.assertIn(location, orphans)
