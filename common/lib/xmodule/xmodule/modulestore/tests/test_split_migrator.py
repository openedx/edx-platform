"""
Tests for split_migrator

"""


import random
import uuid

import mock
import six
from six.moves import range, zip
from xblock.fields import UNIQUE_ID, Reference, ReferenceList, ReferenceValueDict

from openedx.core.lib.tests import attr
from xmodule.modulestore.split_migrator import SplitMigrator
from xmodule.modulestore.tests.test_split_w_old_mongo import SplitWMongoCourseBootstrapper


@attr('mongo')
class TestMigration(SplitWMongoCourseBootstrapper):
    """
    Test the split migrator
    """

    def setUp(self):
        super(TestMigration, self).setUp()
        self.migrator = SplitMigrator(self.split_mongo, self.draft_mongo)

    def _create_course(self):
        """
        A course testing all of the conversion mechanisms:
        * some inheritable settings
        * sequences w/ draft and live intermixed children to ensure all get to the draft but
        only the live ones get to published. Some are only draft, some are both, some are only live.
        * about, static_tab, and conditional documents
        """
        super(TestMigration, self)._create_course(split=False)

        # chapters
        chapter1_name = uuid.uuid4().hex
        self._create_item('chapter', chapter1_name, {}, {'display_name': 'Chapter 1'}, 'course', 'runid', split=False)
        chap2_loc = self.old_course_key.make_usage_key('chapter', uuid.uuid4().hex)
        self._create_item(
            chap2_loc.block_type, chap2_loc.block_id, {}, {'display_name': 'Chapter 2'}, 'course', 'runid', split=False
        )
        # vertical in live only
        live_vert_name = uuid.uuid4().hex
        self._create_item(
            'vertical', live_vert_name, {}, {'display_name': 'Live vertical'}, 'chapter', chapter1_name,
            draft=False, split=False
        )
        self.create_random_units(False, self.old_course_key.make_usage_key('vertical', live_vert_name))
        # vertical in both live and draft
        both_vert_loc = self.old_course_key.make_usage_key('vertical', uuid.uuid4().hex)
        self._create_item(
            both_vert_loc.block_type, both_vert_loc.block_id, {}, {'display_name': 'Both vertical'}, 'chapter', chapter1_name,
            draft=False, split=False
        )
        self.create_random_units(False, both_vert_loc)
        draft_both = self.draft_mongo.get_item(both_vert_loc)
        draft_both.display_name = 'Both vertical renamed'
        self.draft_mongo.update_item(draft_both, self.user_id)
        self.create_random_units(True, both_vert_loc)
        # vertical in draft only (x2)
        draft_vert_loc = self.old_course_key.make_usage_key('vertical', uuid.uuid4().hex)
        self._create_item(
            draft_vert_loc.block_type, draft_vert_loc.block_id, {}, {'display_name': 'Draft vertical'}, 'chapter', chapter1_name,
            draft=True, split=False
        )
        self.create_random_units(True, draft_vert_loc)
        draft_vert_loc = self.old_course_key.make_usage_key('vertical', uuid.uuid4().hex)
        self._create_item(
            draft_vert_loc.block_type, draft_vert_loc.block_id, {}, {'display_name': 'Draft vertical2'}, 'chapter', chapter1_name,
            draft=True, split=False
        )
        self.create_random_units(True, draft_vert_loc)

        # and finally one in live only (so published has to skip 2 preceding sibs)
        live_vert_loc = self.old_course_key.make_usage_key('vertical', uuid.uuid4().hex)
        self._create_item(
            live_vert_loc.block_type, live_vert_loc.block_id, {}, {'display_name': 'Live vertical end'}, 'chapter', chapter1_name,
            draft=False, split=False
        )
        self.create_random_units(False, live_vert_loc)

        # now the other chapter w/ the conditional
        # create pointers to children (before the children exist)
        indirect1_loc = self.old_course_key.make_usage_key('discussion', uuid.uuid4().hex)
        indirect2_loc = self.old_course_key.make_usage_key('html', uuid.uuid4().hex)
        conditional_loc = self.old_course_key.make_usage_key('conditional', uuid.uuid4().hex)
        self._create_item(
            conditional_loc.block_type, conditional_loc.block_id,
            {
                'show_tag_list': [indirect1_loc, indirect2_loc],
                'sources_list': [live_vert_loc, ],
            },
            {
                'xml_attributes': {
                    'completed': True,
                },
            },
            chap2_loc.block_type, chap2_loc.block_id,
            draft=False, split=False
        )
        # create the children
        self._create_item(
            indirect1_loc.block_type, indirect1_loc.block_id, {'data': ""}, {'display_name': 'conditional show 1'},
            conditional_loc.block_type, conditional_loc.block_id,
            draft=False, split=False
        )
        self._create_item(
            indirect2_loc.block_type, indirect2_loc.block_id, {'data': ""}, {'display_name': 'conditional show 2'},
            conditional_loc.block_type, conditional_loc.block_id,
            draft=False, split=False
        )

        # add direct children
        self.create_random_units(False, conditional_loc)

        # and the ancillary docs (not children)
        self._create_item(
            'static_tab', uuid.uuid4().hex, {'data': ""}, {'display_name': 'Tab uno'},
            None, None, draft=False, split=False
        )
        self._create_item(
            'about', 'overview', {'data': "<p>test</p>"}, {},
            None, None, draft=False, split=False
        )
        self._create_item(
            'course_info', 'updates', {'data': "<ol><li><h2>Sep 22</h2><p>test</p></li></ol>"}, {},
            None, None, draft=False, split=False
        )

    def create_random_units(self, draft, parent_loc):
        """
        Create a random selection of units under the given parent w/ random names & attrs
        :param store: which store (e.g., direct/draft) to create them in
        :param parent: the parent to have point to them
        (only makes sense if store is 'direct' and this is 'draft' or vice versa)
        """
        for _ in range(random.randrange(6)):
            location = parent_loc.replace(
                category=random.choice(['html', 'video', 'problem', 'discussion']),
                name=uuid.uuid4().hex
            )
            metadata = {'display_name': str(uuid.uuid4()), 'graded': True}
            data = {}
            self._create_item(
                location.block_type, location.block_id, data, metadata, parent_loc.block_type, parent_loc.block_id,
                draft=draft, split=False
            )

    def compare_courses(self, presplit, new_course_key, published):
        # descend via children to do comparison
        old_root = presplit.get_course(self.old_course_key)
        new_root = self.split_mongo.get_course(new_course_key)
        self.compare_dags(presplit, old_root, new_root, published)

        # grab the detached items to compare they should be in both published and draft
        for category in ['conditional', 'about', 'course_info', 'static_tab']:
            for conditional in presplit.get_items(self.old_course_key, qualifiers={'category': category}):
                locator = new_course_key.make_usage_key(category, conditional.location.block_id)
                self.compare_dags(presplit, conditional, self.split_mongo.get_item(locator), published)

    def compare_dags(self, presplit, presplit_dag_root, split_dag_root, published):
        if split_dag_root.category != 'course':
            self.assertEqual(presplit_dag_root.location.block_id, split_dag_root.location.block_id)
        # compare all fields but references
        for name, field in six.iteritems(presplit_dag_root.fields):
            # fields generated from UNIQUE_IDs are unique to an XBlock's scope,
            # so if such a field is unset on an XBlock, we don't expect it
            # to persist across courses
            field_generated_from_unique_id = not field.is_set_on(presplit_dag_root) and field.default == UNIQUE_ID
            should_check_field = not (
                field_generated_from_unique_id or isinstance(field, (Reference, ReferenceList, ReferenceValueDict))
            )
            if should_check_field:
                self.assertEqual(
                    getattr(presplit_dag_root, name),
                    getattr(split_dag_root, name),
                    u"{}/{}: {} != {}".format(
                        split_dag_root.location, name, getattr(presplit_dag_root, name), getattr(split_dag_root, name)
                    )
                )

        # compare children
        if presplit_dag_root.has_children:
            self.assertEqual(
                # need get_children to filter out drafts
                len(presplit_dag_root.get_children()), len(split_dag_root.children),
                u"{0.category} '{0.display_name}': children  {1} != {2}".format(
                    presplit_dag_root, presplit_dag_root.children, split_dag_root.children
                )
            )
            for pre_child, split_child in zip(presplit_dag_root.get_children(), split_dag_root.get_children()):
                self.compare_dags(presplit, pre_child, split_child, published)

    def test_migrator(self):
        user = mock.Mock(id=1)
        new_course_key = self.migrator.migrate_mongo_course(self.old_course_key, user.id, new_run='new_run')
        # now compare the migrated to the original course
        self.compare_courses(self.draft_mongo, new_course_key, True)  # published
        self.compare_courses(self.draft_mongo, new_course_key, False)  # draft
