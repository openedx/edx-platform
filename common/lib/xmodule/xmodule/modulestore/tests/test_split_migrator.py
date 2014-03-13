"""
Created on Sep 10, 2013

@author: dmitchell

Tests for split_migrator

"""
import unittest
import uuid
import random
import mock
import datetime
from xmodule.fields import Date
from xmodule.modulestore import Location
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.loc_mapper_store import LocMapperStore
from xmodule.modulestore.mongo.draft import DraftModuleStore
from xmodule.modulestore.split_mongo.split import SplitMongoModuleStore
from xmodule.modulestore.mongo.base import MongoModuleStore
from xmodule.modulestore.split_migrator import SplitMigrator
from xmodule.modulestore.mongo import draft
from xmodule.modulestore.tests import test_location_mapper
from xmodule.modulestore.keys import CourseKey


class TestMigration(unittest.TestCase):
    """
    Test the split migrator
    """

    # Snippet of what would be in the django settings envs file
    db_config = {
        'host': 'localhost',
        'db': 'test_xmodule',
        'collection': 'modulestore{0}'.format(uuid.uuid4().hex[:5]),
    }

    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': '',
        'render_template': mock.Mock(return_value=""),
        'xblock_mixins': (InheritanceMixin,)
    }

    def setUp(self):
        super(TestMigration, self).setUp()
        # pylint: disable=W0142
        self.loc_mapper = LocMapperStore(test_location_mapper.TrivialCache(), **self.db_config)
        self.old_mongo = MongoModuleStore(self.db_config, **self.modulestore_options)
        self.draft_mongo = DraftModuleStore(self.db_config, **self.modulestore_options)
        self.split_mongo = SplitMongoModuleStore(
            doc_store_config=self.db_config,
            loc_mapper=self.loc_mapper,
            **self.modulestore_options
        )
        self.migrator = SplitMigrator(self.split_mongo, self.old_mongo, self.draft_mongo, self.loc_mapper)
        self.course_location = None
        self.create_source_course()

    def tearDown(self):
        dbref = self.loc_mapper.db
        dbref.drop_collection(self.loc_mapper.location_map)
        split_db = self.split_mongo.db
        split_db.drop_collection(self.split_mongo.db_connection.course_index)
        split_db.drop_collection(self.split_mongo.db_connection.structures)
        split_db.drop_collection(self.split_mongo.db_connection.definitions)
        # old_mongo doesn't give a db attr, but all of the dbs are the same
        dbref.drop_collection(self.old_mongo.collection)

        dbref.connection.close()

        super(TestMigration, self).tearDown()

    def _create_and_get_item(self, store, location, data, metadata, runtime=None):
        store.create_and_save_xmodule(location, data, metadata, runtime)
        return store.get_item(location)

    def create_source_course(self):
        """
        A course testing all of the conversion mechanisms:
        * some inheritable settings
        * sequences w/ draft and live intermixed children to ensure all get to the draft but
        only the live ones get to published. Some are only draft, some are both, some are only live.
        * about, static_tab, and conditional documents
        """
        location = Location('i4x', 'test_org', 'test_course', 'course', 'runid')
        self.course_location = location
        date_proxy = Date()
        metadata = {
            'start': date_proxy.to_json(datetime.datetime(2000, 3, 13, 4)),
            'display_name': 'Migration test course',
        }
        data = {
            'wiki_slug': 'test_course_slug'
        }
        course_root = self._create_and_get_item(self.old_mongo, location, data, metadata)
        runtime = course_root.runtime
        # chapters
        location = location.replace(category='chapter', name=uuid.uuid4().hex)
        chapter1 = self._create_and_get_item(self.old_mongo, location, {}, {'display_name': 'Chapter 1'}, runtime)
        course_root.children.append(chapter1.location.url())
        location = location.replace(category='chapter', name=uuid.uuid4().hex)
        chapter2 = self._create_and_get_item(self.old_mongo, location, {}, {'display_name': 'Chapter 2'}, runtime)
        course_root.children.append(chapter2.location.url())
        self.old_mongo.update_item(course_root, '**replace_user**')
        # vertical in live only
        location = location.replace(category='vertical', name=uuid.uuid4().hex)
        live_vert = self._create_and_get_item(self.old_mongo, location, {}, {'display_name': 'Live vertical'}, runtime)
        chapter1.children.append(live_vert.location.url())
        self.create_random_units(self.old_mongo, live_vert)
        # vertical in both live and draft
        location = location.replace(category='vertical', name=uuid.uuid4().hex)
        both_vert = self._create_and_get_item(
            self.old_mongo, location, {}, {'display_name': 'Both vertical'}, runtime
        )
        draft_both = self._create_and_get_item(
            self.draft_mongo, location, {}, {'display_name': 'Both vertical renamed'}, runtime
        )
        chapter1.children.append(both_vert.location.url())
        self.create_random_units(self.old_mongo, both_vert, self.draft_mongo, draft_both)
        # vertical in draft only (x2)
        location = location.replace(category='vertical', name=uuid.uuid4().hex)
        draft_vert = self._create_and_get_item(
            self.draft_mongo,
            location, {}, {'display_name': 'Draft vertical'}, runtime)
        chapter1.children.append(draft_vert.location.url())
        self.create_random_units(self.draft_mongo, draft_vert)
        location = location.replace(category='vertical', name=uuid.uuid4().hex)
        draft_vert = self._create_and_get_item(
            self.draft_mongo,
            location, {}, {'display_name': 'Draft vertical2'}, runtime)
        chapter1.children.append(draft_vert.location.url())
        self.create_random_units(self.draft_mongo, draft_vert)
        # and finally one in live only (so published has to skip 2)
        location = location.replace(category='vertical', name=uuid.uuid4().hex)
        live_vert = self._create_and_get_item(
            self.old_mongo,
            location, {}, {'display_name': 'Live vertical end'}, runtime)
        chapter1.children.append(live_vert.location.url())
        self.create_random_units(self.old_mongo, live_vert)

        # update the chapter
        self.old_mongo.update_item(chapter1, '**replace_user**')

        # now the other one w/ the conditional
        # first create some show children
        indirect1 = self._create_and_get_item(
            self.old_mongo,
            location.replace(category='discussion', name=uuid.uuid4().hex),
            "", {'display_name': 'conditional show 1'}, runtime
        )
        indirect2 = self._create_and_get_item(
            self.old_mongo,
            location.replace(category='html', name=uuid.uuid4().hex),
            "", {'display_name': 'conditional show 2'}, runtime
        )
        location = location.replace(category='conditional', name=uuid.uuid4().hex)
        metadata = {
            'xml_attributes': {
                'sources': [live_vert.location.url(), ],
                'completed': True,
            },
        }
        data = {
            'show_tag_list': [indirect1.location.url(), indirect2.location.url()]
        }
        conditional = self._create_and_get_item(self.old_mongo, location, data, metadata, runtime)
        conditional.children = [indirect1.location.url(), indirect2.location.url()]
        # add direct children
        self.create_random_units(self.old_mongo, conditional)
        chapter2.children.append(conditional.location.url())
        self.old_mongo.update_item(chapter2, '**replace_user**')

        # and the ancillary docs (not children)
        location = location.replace(category='static_tab', name=uuid.uuid4().hex)
        # the below automatically adds the tab to the course
        _tab = self._create_and_get_item(self.old_mongo, location, "", {'display_name': 'Tab uno'}, runtime)

        location = location.replace(category='about', name='overview')
        _overview = self._create_and_get_item(self.old_mongo, location, "<p>test</p>", {}, runtime)
        location = location.replace(category='course_info', name='updates')
        _overview = self._create_and_get_item(
            self.old_mongo,
            location, "<ol><li><h2>Sep 22</h2><p>test</p></li></ol>", {}, runtime
        )

    def create_random_units(self, store, parent, cc_store=None, cc_parent=None):
        """
        Create a random selection of units under the given parent w/ random names & attrs
        :param store: which store (e.g., direct/draft) to create them in
        :param parent: the parent to have point to them
        :param cc_store: (optional) if given, make a small change and save also to this store but w/ same location
        (only makes sense if store is 'direct' and this is 'draft' or vice versa)
        """
        for _ in range(random.randrange(6)):
            location = parent.location.replace(
                category=random.choice(['html', 'video', 'problem', 'discussion']),
                name=uuid.uuid4().hex
            )
            metadata = {'display_name': str(uuid.uuid4()), 'graded': True}
            data = {}
            element = self._create_and_get_item(store, location, data, metadata, parent.runtime)
            parent.children.append(element.location.url())
            if cc_store is not None:
                # change display_name and remove graded to test the delta
                element = self._create_and_get_item(
                    cc_store, location, data, {'display_name': str(uuid.uuid4())}, parent.runtime
                )
                cc_parent.children.append(element.location.url())
        store.update_item(parent, '**replace_user**')
        if cc_store is not None:
            cc_store.update_item(cc_parent, '**replace_user**')

    def compare_courses(self, presplit, published):
        # descend via children to do comparison
        old_root = presplit.get_item(self.course_location, depth=None)
        new_root_locator = self.loc_mapper.translate_location(
            self.course_location,
            published,
            add_entry_if_missing=False
        )
        new_root = self.split_mongo.get_course(new_root_locator)
        self.compare_dags(presplit, old_root, new_root, published)

        # grab the detached items to compare they should be in both published and draft
        for category in ['conditional', 'about', 'course_info', 'static_tab']:
            location = self.course_location.replace(name=None, category=category)
            for conditional in presplit.get_items(CourseKey.from_string(location.course_id)):
                locator = self.loc_mapper.translate_location(
                    conditional.location,
                    published,
                    add_entry_if_missing=False
                )
                self.compare_dags(presplit, conditional, self.split_mongo.get_item(locator), published)

    def compare_dags(self, presplit, presplit_dag_root, split_dag_root, published):
        # check that locations match
        self.assertEqual(
            presplit_dag_root.location,
            self.loc_mapper.translate_locator_to_location(split_dag_root.location).replace(revision=None)
        )
        # compare all fields but children
        for name in presplit_dag_root.fields.iterkeys():
            if name != 'children':
                self.assertEqual(
                    getattr(presplit_dag_root, name),
                    getattr(split_dag_root, name),
                    "{}/{}: {} != {}".format(
                        split_dag_root.location, name, getattr(presplit_dag_root, name), getattr(split_dag_root, name)
                    )
                )
        # test split get_item using old Location: old draft store didn't set revision for things above vertical
        # but split does distinguish these; so, set revision if not published
        if not published:
            location = draft.as_draft(presplit_dag_root.location)
        else:
            location = presplit_dag_root.location
        refetched = self.split_mongo.get_item(location)
        self.assertEqual(
            refetched.location, split_dag_root.location,
            "Fetch from split via old Location {} not same as new {}".format(
                refetched.location, split_dag_root.location
            )
        )
        # compare children
        if presplit_dag_root.has_children:
            self.assertEqual(
                len(presplit_dag_root.get_children()), len(split_dag_root.get_children()),
                "{0.category} '{0.display_name}': children count {1} != {2}".format(
                    presplit_dag_root, len(presplit_dag_root.get_children()), split_dag_root.children
                )
            )
            for pre_child, split_child in zip(presplit_dag_root.get_children(), split_dag_root.get_children()):
                self.compare_dags(presplit, pre_child, split_child, published)

    def test_migrator(self):
        user = mock.Mock(id=1)
        self.migrator.migrate_mongo_course(self.course_location, user)
        # now compare the migrated to the original course
        self.compare_courses(self.old_mongo, True)
        self.compare_courses(self.draft_mongo, False)
