import unittest
import mock
import datetime
import uuid
import random

from xmodule.modulestore.inheritance import InheritanceMixin
from opaque_keys.edx.locator import CourseLocator, BlockUsageLocator
from xmodule.modulestore.split_mongo.split import SplitMongoModuleStore
from xmodule.modulestore.mongo import MongoModuleStore, DraftMongoModuleStore
from xmodule.modulestore.mongo.draft import DIRECT_ONLY_CATEGORIES
from xmodule.modulestore import ModuleStoreEnum


class SplitWMongoCourseBoostrapper(unittest.TestCase):
    """
    Helper for tests which need to construct split mongo & old mongo based courses to get interesting internal structure.
    Override _create_course and after invoking the super() _create_course, have it call _create_item for
    each xblock you want in the course.
    This class ensures the db gets created, opened, and cleaned up in addition to creating the course

    Defines the following attrs on self:
    * userid: a random non-registered mock user id
    * split_mongo: a pointer to the split mongo instance
    * old_mongo: a pointer to the old_mongo instance
    * draft_mongo: a pointer to the old draft instance
    * split_course_key (CourseLocator): of the new course
    * old_course_key: the SlashSpecifiedCourseKey for the course
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

    split_course_key = CourseLocator('test_org', 'test_course', 'runid', branch=ModuleStoreEnum.BranchName.draft)

    def setUp(self):
        self.db_config['collection'] = 'modulestore{0}'.format(uuid.uuid4().hex[:5])

        self.userid = random.getrandbits(32)
        super(SplitWMongoCourseBoostrapper, self).setUp()
        self.split_mongo = SplitMongoModuleStore(
            None,
            self.db_config,
            **self.modulestore_options
        )
        self.addCleanup(self.split_mongo.db.connection.close)
        self.addCleanup(self.tear_down_split)
        self.old_mongo = MongoModuleStore(None, self.db_config, **self.modulestore_options)
        self.draft_mongo = DraftMongoModuleStore(
            None, self.db_config, branch_setting_func=lambda: ModuleStoreEnum.Branch.draft_preferred, **self.modulestore_options
        )
        self.addCleanup(self.tear_down_mongo)
        self.old_course_key = None
        self.runtime = None
        self._create_course()

    def tear_down_split(self):
        """
        Remove the test collections, close the db connection
        """
        split_db = self.split_mongo.db
        split_db.drop_collection(split_db.course_index)
        split_db.drop_collection(split_db.structures)
        split_db.drop_collection(split_db.definitions)

    def tear_down_mongo(self):
        """
        Remove the test collections, close the db connection
        """
        split_db = self.split_mongo.db
        # old_mongo doesn't give a db attr, but all of the dbs are the same
        split_db.drop_collection(self.old_mongo.collection)

    def _create_item(self, category, name, data, metadata, parent_category, parent_name, draft=True, split=True):
        """
        Create the item of the given category and block id in split and old mongo, add it to the optional
        parent. The parent category is only needed because old mongo requires it for the id.
        """
        location = self.old_course_key.make_usage_key(category, name)
        if not draft or category in DIRECT_ONLY_CATEGORIES:
            mongo = self.old_mongo
        else:
            mongo = self.draft_mongo
        mongo.create_and_save_xmodule(location, self.userid, definition_data=data, metadata=metadata, runtime=self.runtime)
        if isinstance(data, basestring):
            fields = {'data': data}
        else:
            fields = data.copy()
        fields.update(metadata)
        if parent_name:
            # add child to parent in mongo
            parent_location = self.old_course_key.make_usage_key(parent_category, parent_name)
            if not draft or parent_category in DIRECT_ONLY_CATEGORIES:
                mongo = self.old_mongo
            else:
                mongo = self.draft_mongo
            parent = mongo.get_item(parent_location)
            parent.children.append(location)
            mongo.update_item(parent, self.userid)
            # create pointer for split
            course_or_parent_locator = BlockUsageLocator(
                course_key=self.split_course_key,
                block_type=parent_category,
                block_id=parent_name
            )
        else:
            course_or_parent_locator = self.split_course_key
        if split:
            self.split_mongo.create_item(course_or_parent_locator, category, self.userid, block_id=name, fields=fields)

    def _create_course(self, split=True):
        """
        * some detached items
        * some attached children
        * some orphans
        """
        metadata = {
            'start': datetime.datetime(2000, 3, 13, 4),
            'display_name': 'Migration test course',
        }
        data = {
            'wiki_slug': 'test_course_slug'
        }
        fields = metadata.copy()
        fields.update(data)
        if split:
            # split requires the course to be created separately from creating items
            self.split_mongo.create_course(
                self.split_course_key.org, self.split_course_key.course, self.split_course_key.run, self.userid, fields=fields, root_block_id='runid'
            )
        old_course = self.old_mongo.create_course(self.split_course_key.org, 'test_course', 'runid', self.user_id, fields=fields)
        self.old_course_key = old_course.id
        self.runtime = old_course.runtime
