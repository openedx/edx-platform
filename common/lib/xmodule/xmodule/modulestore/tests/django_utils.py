# encoding: utf-8
"""
Modulestore configuration for test cases.
"""
import copy
import functools
import os
from contextlib import contextmanager

from mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from courseware.field_overrides import OverrideFieldData  # pylint: disable=import-error
from openedx.core.lib.tempdir import mkdtemp_clean

from xmodule.contentstore.django import _CONTENTSTORE
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore, clear_existing_modulestores, SignalHandler
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from xmodule.modulestore.tests.factories import XMODULE_FACTORY_LOCK

from openedx.core.djangoapps.bookmarks.signals import trigger_update_xblocks_cache_task
from openedx.core.djangolib.testing.utils import CacheIsolationMixin, CacheIsolationTestCase


class StoreConstructors(object):
    """Enumeration of store constructor types."""
    draft, split = range(2)


def mixed_store_config(data_dir, mappings, store_order=None):
    """
    Return a `MixedModuleStore` configuration, which provides
    access to both Mongo-backed courses.

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

        store_order (list): List of StoreConstructors providing order of modulestores
            to use in creating courses.
    """
    if store_order is None:
        store_order = [StoreConstructors.draft, StoreConstructors.split]

    store_constructors = {
        StoreConstructors.split: split_mongo_store_config(data_dir)['default'],
        StoreConstructors.draft: draft_mongo_store_config(data_dir)['default'],
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
                'db': 'test_xmodule_{}'.format(os.getpid()),
                'collection': 'modulestore',
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
                'db': 'test_xmodule_{}'.format(os.getpid()),
                'collection': 'modulestore',
            },
            'OPTIONS': modulestore_options
        }
    }

    return store


def contentstore_config():
    """
    Return a new configuration for the contentstore that is isolated
    from other such configurations.
    """
    return {
        'ENGINE': 'xmodule.contentstore.mongo.MongoContentStore',
        'DOC_STORE_CONFIG': {
            'host': MONGO_HOST,
            'db': 'test_xcontent_{}'.format(os.getpid()),
            'port': MONGO_PORT_NUM,
        },
        # allow for additional options that can be keyed on a name, e.g. 'trashcan'
        'ADDITIONAL_OPTIONS': {
            'trashcan': {
                'bucket': 'trash_fs'
            }
        }
    }


@patch('xmodule.modulestore.django.create_modulestore_instance', autospec=True)
def drop_mongo_collections(mock_create):
    """
    If using a Mongo-backed modulestore & contentstore, drop the collections.
    """
    # Do not create the modulestore if it does not exist.
    mock_create.return_value = None

    module_store = modulestore()
    if hasattr(module_store, '_drop_database'):
        module_store._drop_database(database=False)  # pylint: disable=protected-access
    _CONTENTSTORE.clear()
    if hasattr(module_store, 'close_connections'):
        module_store.close_connections()


TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT

# This modulestore will provide a mixed mongo editable modulestore.
# If your test uses the 'toy' course, use the the ToyCourseFactory to construct it.
# If your test needs a closed course to test against, import the common/test/data/2014
#   test course into this modulestore.
# If your test needs a graded course to test against, import the common/test/data/graded
#   test course into this modulestore.
TEST_DATA_MIXED_MODULESTORE = functools.partial(
    mixed_store_config,
    TEST_DATA_DIR,
    {}
)

# All store requests now go through mixed
# Use this modulestore if you specifically want to test mongo and not a mocked modulestore.
TEST_DATA_MONGO_MODULESTORE = functools.partial(mixed_store_config, mkdtemp_clean(), {})

# All store requests now go through mixed
# Use this modulestore if you specifically want to test split-mongo and not a mocked modulestore.
TEST_DATA_SPLIT_MODULESTORE = functools.partial(
    mixed_store_config,
    mkdtemp_clean(),
    {},
    store_order=[StoreConstructors.split, StoreConstructors.draft]
)


class ModuleStoreIsolationMixin(CacheIsolationMixin):
    """
    A mixin to be used by TestCases that want to isolate their use of the
    Modulestore.

    How to use::

        class MyTestCase(ModuleStoreMixin, TestCase):

            MODULESTORE = <settings for the modulestore to test>

            def my_test(self):
                self.start_modulestore_isolation()
                self.addCleanup(self.end_modulestore_isolation)

                modulestore.create_course(...)
                ...

    """

    MODULESTORE = functools.partial(mixed_store_config, mkdtemp_clean(), {})
    CONTENTSTORE = functools.partial(contentstore_config)
    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']
    __settings_overrides = []
    __old_modulestores = []
    __old_contentstores = []

    @classmethod
    def start_modulestore_isolation(cls):
        """
        Isolate uses of the modulestore after this call. Once
        :py:meth:`end_modulestore_isolation` is called, this modulestore will
        be flushed (all content will be deleted).
        """
        cls.start_cache_isolation()
        override = override_settings(
            MODULESTORE=cls.MODULESTORE(),
            CONTENTSTORE=cls.CONTENTSTORE(),
        )

        cls.__old_modulestores.append(copy.deepcopy(settings.MODULESTORE))
        cls.__old_contentstores.append(copy.deepcopy(settings.CONTENTSTORE))
        override.__enter__()
        cls.__settings_overrides.append(override)
        XMODULE_FACTORY_LOCK.enable()
        clear_existing_modulestores()
        cls.store = modulestore()

    @classmethod
    def end_modulestore_isolation(cls):
        """
        Delete all content in the Modulestore, and reset the Modulestore
        settings from before :py:meth:`start_modulestore_isolation` was
        called.
        """
        drop_mongo_collections()  # pylint: disable=no-value-for-parameter
        XMODULE_FACTORY_LOCK.disable()
        cls.__settings_overrides.pop().__exit__(None, None, None)

        assert settings.MODULESTORE == cls.__old_modulestores.pop()
        assert settings.CONTENTSTORE == cls.__old_contentstores.pop()
        cls.end_cache_isolation()


class SharedModuleStoreTestCase(ModuleStoreIsolationMixin, CacheIsolationTestCase):
    """
    Subclass for any test case that uses a ModuleStore that can be shared
    between individual tests. This class ensures that the ModuleStore is cleaned
    before/after the entire test case has run. Use this class if your tests
    set up one or a small number of courses that individual tests do not modify.
    If your tests modify contents in the ModuleStore, you should use
    ModuleStoreTestCase instead.

    How to use::

        from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
        from student.tests.factories import CourseEnrollmentFactory, UserFactory

        class MyModuleStoreTestCase(SharedModuleStoreTestCase):
            @classmethod
            def setUpClass(cls):
                super(MyModuleStoreTestCase, cls).setUpClass()
                cls.course = CourseFactory.create()

            def setUp(self):
                super(MyModuleStoreTestCase, self).setUp()
                self.user = UserFactory.create()
                CourseEnrollmentFactory.create(
                    user=self.user, course_id=self.course.id
                )

    Important things to note:

    1. You're creating the course in setUpClass(), *not* in setUp().
    2. Any Django ORM operations should still happen in setUp(). Models created
       in setUpClass() will *not* be cleaned up, and will leave side-effects
       that can break other, completely unrelated test cases.

    In Django 1.8, we will be able to use setUpTestData() to do class level init
    for Django ORM models that will get cleaned up properly.
    """
    # Tell Django to clean out all databases, not just default
    multi_db = True

    @classmethod
    @contextmanager
    def setUpClassAndTestData(cls):  # pylint: disable=invalid-name
        """
        For use when the test class has a setUpTestData() method that uses variables
        that are setup during setUpClass() of the same test class.
        Use it like so:
        @classmethod
        def setUpClass(cls):
            with super(MyTestClass, cls).setUpClassAndTestData():
                <all the cls.setUpClass() setup code that performs modulestore setup...>
        @classmethod
        def setUpTestData(cls):
            <all the setup code that creates Django models per test class...>
            <these models can use variables (courses) setup in setUpClass() above>
        """
        cls.start_modulestore_isolation()
        # Now yield to allow the test class to run its setUpClass() setup code.
        yield
        # Now call the base class, which calls back into the test class's setUpTestData().
        super(SharedModuleStoreTestCase, cls).setUpClass()

    @classmethod
    def setUpClass(cls):
        """
        Start modulestore isolation, and then load modulestore specific
        test data.
        """
        super(SharedModuleStoreTestCase, cls).setUpClass()
        cls.start_modulestore_isolation()

    @classmethod
    def tearDownClass(cls):
        cls.end_modulestore_isolation()
        super(SharedModuleStoreTestCase, cls).tearDownClass()

    def setUp(self):
        # OverrideFieldData.provider_classes is always reset to `None` so
        # that they're recalculated for every test
        OverrideFieldData.provider_classes = None
        super(SharedModuleStoreTestCase, self).setUp()


class ModuleStoreTestCase(ModuleStoreIsolationMixin, TestCase):
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

    CREATE_USER = True

    # Tell Django to clean out all databases, not just default
    multi_db = True

    def setUp(self):
        """
        Creates a test User if `self.CREATE_USER` is True.
        Sets the password as self.user_password.
        """
        self.start_modulestore_isolation()

        self.addCleanup(self.end_modulestore_isolation)

        # When testing CCX, we should make sure that
        # OverrideFieldData.provider_classes is always reset to `None` so
        # that they're recalculated for every test
        OverrideFieldData.provider_classes = None

        super(ModuleStoreTestCase, self).setUp()

        SignalHandler.course_published.disconnect(trigger_update_xblocks_cache_task)

        self.store = modulestore()

        uname = 'testuser'
        email = 'test+courses@edx.org'
        self.user_password = 'foo'

        if self.CREATE_USER:
            # Create the user so we can log them in.
            self.user = User.objects.create_user(uname, email, self.user_password)

            # Note that we do not actually need to do anything
            # for registration if we directly mark them active.
            self.user.is_active = True

            # Staff has access to view all courses
            self.user.is_staff = True
            self.user.save()

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

    def create_staff_user(self):
        """
        Creates a staff test user.
        Returns the staff test user and its password.
        """
        uname = 'teststaff'
        password = 'bar'
        staff_user = User.objects.create_user(uname, 'test+staff@edx.org', password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        staff_user.is_active = True
        staff_user.is_staff = True
        staff_user.save()
        return staff_user, password

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
