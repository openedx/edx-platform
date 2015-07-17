# encoding: utf-8
"""
Modulestore configuration for test cases.
"""
import datetime
import pytz
from uuid import uuid4

from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings
from request_cache.middleware import RequestCache

from courseware.field_overrides import OverrideFieldData  # pylint: disable=import-error
from openedx.core.lib.tempdir import mkdtemp_clean

from xmodule.contentstore.django import _CONTENTSTORE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from xmodule.modulestore.tests.sample_courses import default_block_info_tree, TOY_BLOCK_INFO_TREE
from xmodule.modulestore.tests.factories import XMODULE_FACTORY_LOCK


class StoreConstructors(object):
    """Enumeration of store constructor types."""
    draft, split, xml = range(3)


def mixed_store_config(data_dir, mappings, include_xml=False, xml_source_dirs=None, store_order=None):
    """
    Return a `MixedModuleStore` configuration, which provides
    access to both Mongo- and XML-backed courses.

    Args:
        data_dir (string): the directory from which to load XML-backed courses.
        mappings (string): a dictionary mapping course IDs to modulestores, for example:

            {
                'MITx/2.01x/2013_Spring': 'xml',
                'edx/999/2013_Spring': 'default'
            }

        where 'xml' and 'default' are the two options provided by this configuration,
        mapping (respectively) to XML-backed and Mongo-backed modulestores..

    Keyword Args:

        include_xml (boolean): If True, include an XML modulestore in the configuration.
        xml_source_dirs (list): The directories containing XML courses to load from disk.

        note: For the courses to be loaded into the XML modulestore and accessible do the following:
            * include_xml should be True
            * xml_source_dirs should be the list of directories (relative to data_dir)
                  containing the courses you want to load
            * mappings should be configured, pointing the xml courses to the xml modulestore

    """
    if store_order is None:
        store_order = [StoreConstructors.draft, StoreConstructors.split]

    if include_xml and StoreConstructors.xml not in store_order:
        store_order.append(StoreConstructors.xml)

    store_constructors = {
        StoreConstructors.split: split_mongo_store_config(data_dir)['default'],
        StoreConstructors.draft: draft_mongo_store_config(data_dir)['default'],
        StoreConstructors.xml: xml_store_config(data_dir, source_dirs=xml_source_dirs)['default'],
    }

    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
            'OPTIONS': {
                'mappings': mappings,
                'stores': [store_constructors[store] for store in store_order],
            }
        }
    }
    return store


def draft_mongo_store_config(data_dir):
    """
    Defines default module store using DraftMongoModuleStore.
    """

    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': data_dir,
        'render_template': 'edxmako.shortcuts.render_to_string'
    }

    store = {
        'default': {
            'NAME': 'draft',
            'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
            'DOC_STORE_CONFIG': {
                'host': MONGO_HOST,
                'port': MONGO_PORT_NUM,
                'db': 'test_xmodule',
                'collection': 'modulestore_{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': modulestore_options
        }
    }

    return store


def split_mongo_store_config(data_dir):
    """
    Defines split module store.
    """
    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': data_dir,
        'render_template': 'edxmako.shortcuts.render_to_string',
    }

    store = {
        'default': {
            'NAME': 'draft',
            'ENGINE': 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore',
            'DOC_STORE_CONFIG': {
                'host': MONGO_HOST,
                'port': MONGO_PORT_NUM,
                'db': 'test_xmodule',
                'collection': 'modulestore_{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': modulestore_options
        }
    }

    return store


def xml_store_config(data_dir, source_dirs=None):
    """
    Defines default module store using XMLModuleStore.

    Note: you should pass in a list of source_dirs that you care about,
    otherwise all courses in the data_dir will be processed.
    """
    store = {
        'default': {
            'NAME': 'xml',
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
                'source_dirs': source_dirs,
            }
        }
    }

    return store

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT

# This is an XML only modulestore with only the toy course loaded
TEST_DATA_XML_MODULESTORE = xml_store_config(TEST_DATA_DIR, source_dirs=['toy'])

# This modulestore will provide both a mixed mongo editable modulestore, and
# an XML store with just the toy course loaded.
TEST_DATA_MIXED_TOY_MODULESTORE = mixed_store_config(
    TEST_DATA_DIR, {'edX/toy/2012_Fall': 'xml', }, include_xml=True, xml_source_dirs=['toy']
)

# This modulestore will provide both a mixed mongo editable modulestore, and
# an XML store with common/test/data/2014 loaded, which is a course that is closed.
TEST_DATA_MIXED_CLOSED_MODULESTORE = mixed_store_config(
    TEST_DATA_DIR, {'edX/detached_pages/2014': 'xml', }, include_xml=True, xml_source_dirs=['2014']
)

# This modulestore will provide both a mixed mongo editable modulestore, and
# an XML store with common/test/data/graded loaded, which is a course that is graded.
TEST_DATA_MIXED_GRADED_MODULESTORE = mixed_store_config(
    TEST_DATA_DIR, {'edX/graded/2012_Fall': 'xml', }, include_xml=True, xml_source_dirs=['graded']
)

# All store requests now go through mixed
# Use this modulestore if you specifically want to test mongo and not a mocked modulestore.
# This modulestore definition below will not load any xml courses.
TEST_DATA_MONGO_MODULESTORE = mixed_store_config(mkdtemp_clean(), {}, include_xml=False)

# All store requests now go through mixed
# Use this modulestore if you specifically want to test split-mongo and not a mocked modulestore.
# This modulestore definition below will not load any xml courses.
TEST_DATA_SPLIT_MODULESTORE = mixed_store_config(
    mkdtemp_clean(),
    {},
    include_xml=False,
    store_order=[StoreConstructors.split, StoreConstructors.draft]
)


class ModuleStoreTestCase(TestCase):
    """
    Subclass for any test case that uses a ModuleStore.
    Ensures that the ModuleStore is cleaned before/after each test.

    Usage:

        1. Create a subclass of `ModuleStoreTestCase`
        2. (optional) If you need a specific variety of modulestore, or particular ModuleStore
           options, set the MODULESTORE class attribute of your test class to the
           appropriate modulestore config.

           For example:

               class FooTest(ModuleStoreTestCase):
                   MODULESTORE = mixed_store_config(data_dir, mappings)
                   # ...

        3. Use factories (e.g. `CourseFactory`, `ItemFactory`) to populate
           the modulestore with test data.

    NOTE:
        * For Mongo-backed courses (created with `CourseFactory`),
          the state of the course will be reset before/after each
          test method executes.

        * For XML-backed courses, the course state will NOT
          reset between test methods (although it will reset
          between test classes)

          The reason is: XML courses are not editable, so to reset
          a course you have to reload it from disk, which is slow.

          If you do need to reset an XML course, use
          `clear_existing_modulestores()` directly in
          your `setUp()` method.
    """

    MODULESTORE = mixed_store_config(mkdtemp_clean(), {}, include_xml=False)

    def setUp(self, **kwargs):
        """
        Creates a test User if `create_user` is True.
        Returns the password for the test User.

        Args:
            create_user - specifies whether or not to create a test User.  Default is True.
        """
        settings_override = override_settings(MODULESTORE=self.MODULESTORE)
        settings_override.__enter__()
        self.addCleanup(settings_override.__exit__, None, None, None)

        # Clear out any existing modulestores,
        # which will cause them to be re-created
        clear_existing_modulestores()

        self.addCleanup(self.drop_mongo_collections)

        self.addCleanup(RequestCache().clear_request_cache)

        # Enable XModuleFactories for the space of this test (and its setUp).
        self.addCleanup(XMODULE_FACTORY_LOCK.disable)
        XMODULE_FACTORY_LOCK.enable()

        # When testing CCX, we should make sure that
        # OverrideFieldData.provider_classes is always reset to `None` so
        # that they're recalculated for every test
        OverrideFieldData.provider_classes = None

        super(ModuleStoreTestCase, self).setUp()

        self.store = modulestore()

        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        if kwargs.pop('create_user', True):
            # Create the user so we can log them in.
            self.user = User.objects.create_user(uname, email, password)

            # Note that we do not actually need to do anything
            # for registration if we directly mark them active.
            self.user.is_active = True

            # Staff has access to view all courses
            self.user.is_staff = True
            self.user.save()

        return password

    def create_non_staff_user(self):
        """
        Creates a non-staff test user.
        Returns the non-staff test user and its password.
        """
        uname = 'teststudent'
        password = 'foo'
        nonstaff_user = User.objects.create_user(uname, 'test+student@edx.org', password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        nonstaff_user.is_active = True
        nonstaff_user.is_staff = False
        nonstaff_user.save()
        return nonstaff_user, password

    def update_course(self, course, user_id):
        """
        Updates the version of course in the modulestore

        'course' is an instance of CourseDescriptor for which we want
        to update metadata.
        """
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, course.id):
            self.store.update_item(course, user_id)
        updated_course = self.store.get_course(course.id)
        return updated_course

    @staticmethod
    @patch('xmodule.modulestore.django.create_modulestore_instance')
    def drop_mongo_collections(mock_create):
        """
        If using a Mongo-backed modulestore & contentstore, drop the collections.
        """
        # Do not create the modulestore if it does not exist.
        mock_create.return_value = None

        module_store = modulestore()
        if hasattr(module_store, '_drop_database'):
            module_store._drop_database()  # pylint: disable=protected-access
        _CONTENTSTORE.clear()
        if hasattr(module_store, 'close_connections'):
            module_store.close_connections()

    def create_sample_course(self, org, course, run, block_info_tree=None, course_fields=None):
        """
        create a course in the default modulestore from the collection of BlockInfo
        records defining the course tree
        Returns:
            course_loc: the CourseKey for the created course
        """
        if block_info_tree is None:
            block_info_tree = default_block_info_tree

        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, None):
            course = self.store.create_course(org, course, run, self.user.id, fields=course_fields)
            self.course_loc = course.location  # pylint: disable=attribute-defined-outside-init

            def create_sub_tree(parent_loc, block_info):
                """Recursively creates a sub_tree on this parent_loc with this block."""
                block = self.store.create_child(
                    self.user.id,
                    # TODO remove version_agnostic() when we impl the single transaction
                    parent_loc.version_agnostic(),
                    block_info.category, block_id=block_info.block_id,
                    fields=block_info.fields,
                )
                for tree in block_info.sub_tree:
                    create_sub_tree(block.location, tree)
                setattr(self, block_info.block_id, block.location.version_agnostic())

            for tree in block_info_tree:
                create_sub_tree(self.course_loc, tree)

            # remove version_agnostic when bulk write works
            self.store.publish(self.course_loc.version_agnostic(), self.user.id)
        return self.course_loc.course_key.version_agnostic()

    def create_toy_course(self, org='edX', course='toy', run='2012_Fall'):
        """
        Create an equivalent to the toy xml course
        """
#        with self.store.bulk_operations(self.store.make_course_key(org, course, run)):
        self.toy_loc = self.create_sample_course(  # pylint: disable=attribute-defined-outside-init
            org, course, run, TOY_BLOCK_INFO_TREE,
            {
                "textbooks": [["Textbook", "https://s3.amazonaws.com/edx-textbooks/guttag_computation_v3/"]],
                "wiki_slug": "toy",
                "display_name": "Toy Course",
                "graded": True,
                "discussion_topics": {"General": {"id": "i4x-edX-toy-course-2012_Fall"}},
                "graceperiod": datetime.timedelta(days=2, seconds=21599),
                "start": datetime.datetime(2015, 07, 17, 12, tzinfo=pytz.utc),
                "xml_attributes": {"filename": ["course/2012_Fall.xml", "course/2012_Fall.xml"]},
                "pdf_textbooks": [
                    {
                        "tab_title": "Sample Multi Chapter Textbook",
                        "id": "MyTextbook",
                        "chapters": [
                            {"url": "/static/Chapter1.pdf", "title": "Chapter 1"},
                            {"url": "/static/Chapter2.pdf", "title": "Chapter 2"}
                        ]
                    }
                ],
                "course_image": "just_a_test.jpg",
            }
        )
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.toy_loc):
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="short_description",
                fields={"data": "A course about toys."}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="effort",
                fields={"data": "6 hours"}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="end_date",
                fields={"data": "TBD"}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "course_info", "handouts",
                fields={"data": "<a href='/static/handouts/sample_handout.txt'>Sample</a>"}
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "static_tab", "resources",
                fields={"display_name": "Resources"},
            )
            self.store.create_item(
                self.user.id, self.toy_loc, "static_tab", "syllabus",
                fields={"display_name": "Syllabus"},
            )
        return self.toy_loc
