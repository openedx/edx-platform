# encoding: utf-8
"""
Modulestore configuration for test cases.
"""

from uuid import uuid4
from django.test import TestCase
from django.contrib.auth.models import User
from xmodule.contentstore.django import _CONTENTSTORE
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from xmodule.modulestore import ModuleStoreEnum
import datetime
import pytz
from xmodule.tabs import CoursewareTab, CourseInfoTab, StaticTab, DiscussionTab, ProgressTab, WikiTab
from xmodule.modulestore.tests.sample_courses import default_block_info_tree, TOY_BLOCK_INFO_TREE


def mixed_store_config(data_dir, mappings):
    """
    Return a `MixedModuleStore` configuration, which provides
    access to both Mongo- and XML-backed courses.

    `data_dir` is the directory from which to load XML-backed courses.
    `mappings` is a dictionary mapping course IDs to modulestores, for example:

        {
            'MITx/2.01x/2013_Spring': 'xml',
            'edx/999/2013_Spring': 'default'
        }

    where 'xml' and 'default' are the two options provided by this configuration,
    mapping (respectively) to XML-backed and Mongo-backed modulestores..
    """
    draft_mongo_config = draft_mongo_store_config(data_dir)
    xml_config = xml_store_config(data_dir)
    split_mongo = split_mongo_store_config(data_dir)

    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
            'OPTIONS': {
                'mappings': mappings,
                'stores': [
                    draft_mongo_config['default'],
                    split_mongo['default'],
                    xml_config['default'],
                ]
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
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
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
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': modulestore_options
        }
    }

    return store


def xml_store_config(data_dir):
    """
    Defines default module store using XMLModuleStore.
    """
    store = {
        'default': {
            'NAME': 'xml',
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

    return store




class ModuleStoreTestCase(TestCase):
    """
    Subclass for any test case that uses a ModuleStore.
    Ensures that the ModuleStore is cleaned before/after each test.

    Usage:

        1. Create a subclass of `ModuleStoreTestCase`
        2. Use Django's @override_settings decorator to use
           the desired modulestore configuration.

           For example:

               MIXED_CONFIG = mixed_store_config(data_dir, mappings)

               @override_settings(MODULESTORE=MIXED_CONFIG)
               class FooTest(ModuleStoreTestCase):
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
    def setUp(self, **kwargs):
        """
        Creates a test User if `create_user` is True.
        Returns the password for the test User.

        Args:
            create_user - specifies whether or not to create a test User.  Default is True.
        """
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
    def drop_mongo_collections():
        """
        If using a Mongo-backed modulestore & contentstore, drop the collections.
        """
        module_store = modulestore()
        if hasattr(module_store, '_drop_database'):
            module_store._drop_database()  # pylint: disable=protected-access
        _CONTENTSTORE.clear()

    @classmethod
    def setUpClass(cls):
        """
        Delete the existing modulestores, causing them to be reloaded.
        """
        # Clear out any existing modulestores,
        # which will cause them to be re-created
        # the next time they are accessed.
        clear_existing_modulestores()
        TestCase.setUpClass()

    def _pre_setup(self):
        """
        Flush the ModuleStore.
        """

        # Flush the Mongo modulestore
        self.drop_mongo_collections()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._pre_setup()

    def _post_teardown(self):
        """
        Flush the ModuleStore after each test.
        """
        self.drop_mongo_collections()
        # Clear out the existing modulestores,
        # which will cause them to be re-created
        # the next time they are accessed.
        # We do this at *both* setup and teardown just to be safe.
        clear_existing_modulestores()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._post_teardown()

    def create_sample_course(self, org, course, run, block_info_tree=default_block_info_tree, course_fields=None):
        """
        create a course in the default modulestore from the collection of BlockInfo
        records defining the course tree
        Returns:
            course_loc: the CourseKey for the created course
        """
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, None):
#             with self.store.bulk_write_operations(self.store.make_course_key(org, course, run)):
                course = self.store.create_course(org, course, run, self.user.id, fields=course_fields)
                self.course_loc = course.location

                def create_sub_tree(parent_loc, block_info):
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
#        with self.store.bulk_write_operations(self.store.make_course_key(org, course, run)):
        self.toy_loc = self.create_sample_course(
            org, course, run, TOY_BLOCK_INFO_TREE,
            {
                "textbooks" : [["Textbook", "https://s3.amazonaws.com/edx-textbooks/guttag_computation_v3/"]],
                "wiki_slug" : "toy",
                "display_name" : "Toy Course",
                "graded" : True,
                "tabs" : [
                     CoursewareTab(),
                     CourseInfoTab(),
                     StaticTab(name="Syllabus", url_slug="syllabus"),
                     StaticTab(name="Resources", url_slug="resources"),
                     DiscussionTab(),
                     WikiTab(),
                     ProgressTab(),
                ],
                "discussion_topics" : {"General" : {"id" : "i4x-edX-toy-course-2012_Fall"}},
                "graceperiod" : datetime.timedelta(days=2, seconds=21599),
                "start" : datetime.datetime(2015, 07, 17, 12, tzinfo=pytz.utc),
                "xml_attributes" : {"filename" : ["course/2012_Fall.xml", "course/2012_Fall.xml"]},
                "pdf_textbooks" : [
                    {
                        "tab_title" : "Sample Multi Chapter Textbook",
                        "id" : "MyTextbook",
                        "chapters" : [
                             {"url" : "/static/Chapter1.pdf", "title" : "Chapter 1"},
                             {"url" : "/static/Chapter2.pdf", "title" : "Chapter 2"}
                        ]
                     }
                ],
                "course_image" : "just_a_test.jpg",
            }
        )
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.toy_loc):
            self.store.create_item(
                self.user.id, self.toy_loc, "about", block_id="short_description",
                fields={"data" : "A course about toys."}
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
