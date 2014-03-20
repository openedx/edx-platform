"""
Test the publish code (primary causing orphans)
"""
import uuid
import mock
import unittest
import datetime
import random

from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.mongo import MongoModuleStore, DraftMongoModuleStore
from xmodule.modulestore import Location
from xmodule.fields import Date
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.mongo.draft import DIRECT_ONLY_CATEGORIES


class TestPublish(unittest.TestCase):
    """
    Test the publish code (primary causing orphans)
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

    def setUp(self):
        self.db_config['collection'] = 'modulestore{0}'.format(uuid.uuid4().hex[:5])

        self.old_mongo = MongoModuleStore(self.db_config, **self.modulestore_options)
        self.draft_mongo = DraftMongoModuleStore(self.db_config, **self.modulestore_options)
        self.addCleanup(self.tear_down_mongo)
        self.course_location = None

    def tear_down_mongo(self):
        # old_mongo doesn't give a db attr, but all of the dbs are the same and draft and pub use same collection
        dbref = self.old_mongo.collection.database
        dbref.drop_collection(self.old_mongo.collection)
        dbref.connection.close()

    def _create_item(self, category, name, data, metadata, parent_category, parent_name, runtime):
        """
        Create the item in either draft or direct based on category and attach to its parent.
        """
        location = self.course_location.replace(category=category, name=name)
        if category in DIRECT_ONLY_CATEGORIES:
            mongo = self.old_mongo
        else:
            mongo = self.draft_mongo
        mongo.create_and_save_xmodule(location, data, metadata, runtime)
        if isinstance(data, basestring):
            fields = {'data': data}
        else:
            fields = data.copy()
        fields.update(metadata)
        if parent_name:
            # add child to parent in mongo
            parent_location = self.course_location.replace(category=parent_category, name=parent_name)
            parent = self.draft_mongo.get_item(parent_location)
            parent.children.append(location.url())
            if parent_category in DIRECT_ONLY_CATEGORIES:
                mongo = self.old_mongo
            else:
                mongo = self.draft_mongo
            mongo.update_item(parent, '**replace_user**')

    def _create_course(self):
        """
        Create the course, publish all verticals
        * some detached items
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

        self.course_location = Location('test_org', 'test_course', 'course', 'runid')
        self.old_mongo.create_and_save_xmodule(self.course_location, data, metadata)
        runtime = self.draft_mongo.get_item(self.course_location).runtime

        self._create_item('chapter', 'Chapter1', {}, {'display_name': 'Chapter 1'}, 'course', 'runid', runtime)
        self._create_item('chapter', 'Chapter2', {}, {'display_name': 'Chapter 2'}, 'course', 'runid', runtime)
        self._create_item('vertical', 'Vert1', {}, {'display_name': 'Vertical 1'}, 'chapter', 'Chapter1', runtime)
        self._create_item('vertical', 'Vert2', {}, {'display_name': 'Vertical 2'}, 'chapter', 'Chapter1', runtime)
        self._create_item('html', 'Html1', "<p>Goodbye</p>", {'display_name': 'Parented Html'}, 'vertical', 'Vert1', runtime)
        self._create_item(
            'discussion', 'Discussion1',
            "discussion discussion_category=\"Lecture 1\" discussion_id=\"a08bfd89b2aa40fa81f2c650a9332846\" discussion_target=\"Lecture 1\"/>\n",
            {
                "discussion_category": "Lecture 1",
                "discussion_target": "Lecture 1",
                "display_name": "Lecture 1 Discussion",
                "discussion_id": "a08bfd89b2aa40fa81f2c650a9332846"
            },
            'vertical', 'Vert1', runtime
        )
        self._create_item('html', 'Html2', "<p>Hellow</p>", {'display_name': 'Hollow Html'}, 'vertical', 'Vert1', runtime)
        self._create_item(
            'discussion', 'Discussion2',
            "discussion discussion_category=\"Lecture 2\" discussion_id=\"b08bfd89b2aa40fa81f2c650a9332846\" discussion_target=\"Lecture 2\"/>\n",
            {
                "discussion_category": "Lecture 2",
                "discussion_target": "Lecture 2",
                "display_name": "Lecture 2 Discussion",
                "discussion_id": "b08bfd89b2aa40fa81f2c650a9332846"
            },
            'vertical', 'Vert2', runtime
        )
        self._create_item('static_tab', 'staticuno', "<p>tab</p>", {'display_name': 'Tab uno'}, None, None, runtime)
        self._create_item('about', 'overview', "<p>overview</p>", {}, None, None, runtime)
        self._create_item('course_info', 'updates', "<ol><li><h2>Sep 22</h2><p>test</p></li></ol>", {}, None, None, runtime)

    def _xmodule_recurse(self, item, action):
        """
        Applies action depth-first down tree and to item last.

        A copy of  cms.djangoapps.contentstore.views.helpers._xmodule_recurse to reproduce its use and behavior
        outside of django.
        """
        for child in item.get_children():
            self._xmodule_recurse(child, action)

        action(item)

    def test_publish_draft_delete(self):
        """
        To reproduce a bug (STUD-811) publish a vertical, convert to draft, delete a child, move a child, publish.
        See if deleted and moved children still is connected or exists in db (bug was disconnected but existed)
        """
        self._create_course()
        userid = random.getrandbits(32)
        location = self.course_location.replace(category='vertical', name='Vert1')
        item = self.draft_mongo.get_item(location, 2)
        self._xmodule_recurse(
            item,
            lambda i: self.draft_mongo.publish(i.location, userid)
        )
        # verify status
        item = self.draft_mongo.get_item(location, 0)
        self.assertFalse(getattr(item, 'is_draft', False), "Item was published. Draft should not exist")
        # however, children are still draft, but I'm not sure that's by design

        # convert back to draft
        self.draft_mongo.convert_to_draft(location)
        # both draft and published should exist
        draft_vert = self.draft_mongo.get_item(location, 0)
        self.assertTrue(getattr(draft_vert, 'is_draft', False), "Item was converted to draft but doesn't say so")
        item = self.old_mongo.get_item(location, 0)
        self.assertFalse(getattr(item, 'is_draft', False), "Published item doesn't say so")

        # delete the discussion (which oddly is not in draft mode)
        location = self.course_location.replace(category='discussion', name='Discussion1')
        self.draft_mongo.delete_item(location)
        # remove pointer from draft vertical (verify presence first to ensure process is valid)
        self.assertIn(location.url(), draft_vert.children)
        draft_vert.children.remove(location.url())
        # move the other child
        other_child_loc = self.course_location.replace(category='html', name='Html2')
        draft_vert.children.remove(other_child_loc.url())
        other_vert = self.draft_mongo.get_item(self.course_location.replace(category='vertical', name='Vert2'), 0)
        other_vert.children.append(other_child_loc.url())
        self.draft_mongo.update_item(draft_vert, '**replace_user**')
        self.draft_mongo.update_item(other_vert, '**replace_user**')
        # publish
        self._xmodule_recurse(
            draft_vert,
            lambda i: self.draft_mongo.publish(i.location, userid)
        )
        item = self.old_mongo.get_item(draft_vert.location, 0)
        self.assertNotIn(location.url(), item.children)
        with self.assertRaises(ItemNotFoundError):
            self.draft_mongo.get_item(location)
        self.assertNotIn(other_child_loc.url(), item.children)
        self.assertTrue(self.draft_mongo.has_item(None, other_child_loc), "Oops, lost moved item")
