import pprint
import pymongo.message

from factory import Factory, lazy_attribute_sequence, lazy_attribute
from factory.containers import CyclicDefinitionError
from uuid import uuid4

from xmodule.modulestore import prefer_xmodules, ModuleStoreEnum
from opaque_keys.edx.locations import Location
from opaque_keys.edx.keys import UsageKey
from xblock.core import XBlock
from xmodule.tabs import StaticTab
from decorator import contextmanager
from mock import Mock, patch
from nose.tools import assert_less_equal, assert_greater_equal
import factory
import threading
from xmodule.modulestore.django import modulestore


class Dummy(object):
    pass


class XModuleFactoryLock(threading.local):
    """
    This class exists to store whether XModuleFactory can be accessed in a safe
    way (meaning, in a context where the data it creates will be cleaned up).

    Users of XModuleFactory (or its subclasses) should only call XModuleFactoryLock.enable
    after ensuring that a) the modulestore will be cleaned up, and b) that XModuleFactoryLock.disable
    will be called.
    """
    def __init__(self):
        super(XModuleFactoryLock, self).__init__()
        self._enabled = False

    def enable(self):
        """
        Enable XModuleFactories. This should only be turned in a context
        where the modulestore will be reset at the end of the test (such
        as inside ModuleStoreTestCase).
        """
        self._enabled = True

    def disable(self):
        """
        Disable XModuleFactories. This should be called once the data
        from the factory has been cleaned up.
        """
        self._enabled = False

    def is_enabled(self):
        """
        Return whether XModuleFactories are enabled.
        """
        return self._enabled


XMODULE_FACTORY_LOCK = XModuleFactoryLock()


class XModuleFactory(Factory):
    """
    Factory for XModules
    """

    # We have to give a Factory a FACTORY_FOR.
    # However, the class that we create is actually determined by the category
    # specified in the factory
    FACTORY_FOR = Dummy

    @lazy_attribute
    def modulestore(self):
        msg = "XMODULE_FACTORY_LOCK not enabled. Please use ModuleStoreTestCase as your test baseclass."
        assert XMODULE_FACTORY_LOCK.is_enabled(), msg

        from xmodule.modulestore.django import modulestore
        return modulestore()


last_course = threading.local()


class CourseFactory(XModuleFactory):
    """
    Factory for XModule courses.
    """
    org = factory.Sequence(lambda n: 'org.%d' % n)
    number = factory.Sequence(lambda n: 'course_%d' % n)
    display_name = factory.Sequence(lambda n: 'Run %d' % n)

    # pylint: disable=unused-argument
    @classmethod
    def _create(cls, target_class, **kwargs):

        # All class attributes (from this class and base classes) are
        # passed in via **kwargs. However, some of those aren't actual field values,
        # so pop those off for use separately
        org = kwargs.pop('org', None)
        # because the factory provides a default 'number' arg, prefer the non-defaulted 'course' arg if any
        number = kwargs.pop('course', kwargs.pop('number', None))
        store = kwargs.pop('modulestore')
        name = kwargs.get('name', kwargs.get('run', Location.clean(kwargs.get('display_name'))))
        run = kwargs.pop('run', name)
        user_id = kwargs.pop('user_id', ModuleStoreEnum.UserID.test)

        # Pass the metadata just as field=value pairs
        kwargs.update(kwargs.pop('metadata', {}))
        default_store_override = kwargs.pop('default_store', None)

        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            if default_store_override is not None:
                with store.default_store(default_store_override):
                    new_course = store.create_course(org, number, run, user_id, fields=kwargs)
            else:
                new_course = store.create_course(org, number, run, user_id, fields=kwargs)

            last_course.loc = new_course.location
            return new_course


class LibraryFactory(XModuleFactory):
    """
    Factory for creating a content library
    """
    org = factory.Sequence('org{}'.format)
    library = factory.Sequence('lib{}'.format)
    display_name = factory.Sequence('Test Library {}'.format)

    # pylint: disable=unused-argument
    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Create a library with a unique name and key.
        All class attributes (from this class and base classes) are automagically
        passed in via **kwargs.
        """
        # some of the kwargst actual field values, so pop those off for use separately:
        org = kwargs.pop('org')
        library = kwargs.pop('library')
        store = kwargs.pop('modulestore')
        user_id = kwargs.pop('user_id', ModuleStoreEnum.UserID.test)

        # Pass the metadata just as field=value pairs
        kwargs.update(kwargs.pop('metadata', {}))
        default_store_override = kwargs.pop('default_store', ModuleStoreEnum.Type.split)
        with store.default_store(default_store_override):
            new_library = store.create_library(org, library, user_id, fields=kwargs)
            return new_library


class ItemFactory(XModuleFactory):
    """
    Factory for XModule items.
    """

    category = 'chapter'
    parent = None

    @lazy_attribute_sequence
    def display_name(self, n):
        return "{} {}".format(self.category, n)

    @lazy_attribute
    def location(self):
        if self.display_name is None:
            dest_name = uuid4().hex
        else:
            dest_name = self.display_name.replace(" ", "_")

        new_location = self.parent_location.course_key.make_usage_key(
            self.category,
            dest_name
        )
        return new_location

    @lazy_attribute
    def parent_location(self):
        default_location = getattr(last_course, 'loc', None)
        try:
            parent = self.parent
        # This error is raised if the caller hasn't provided either parent or parent_location
        # In this case, we'll just return the default parent_location
        except CyclicDefinitionError:
            return default_location

        if parent is None:
            return default_location

        return parent.location

    @classmethod
    def _create(cls, target_class, **kwargs):
        """
        Uses ``**kwargs``:

        :parent_location: (required): the location of the parent module
            (e.g. the parent course or section)

        :category: the category of the resulting item.

        :data: (optional): the data for the item
            (e.g. XML problem definition for a problem item)

        :display_name: (optional): the display name of the item

        :metadata: (optional): dictionary of metadata attributes

        :boilerplate: (optional) the boilerplate for overriding field values

        :publish_item: (optional) whether or not to publish the item (default is True)

        :target_class: is ignored
        """

        # All class attributes (from this class and base classes) are
        # passed in via **kwargs. However, some of those aren't actual field values,
        # so pop those off for use separately

        # catch any old style users before they get into trouble
        assert 'template' not in kwargs
        parent_location = kwargs.pop('parent_location', None)
        data = kwargs.pop('data', None)
        category = kwargs.pop('category', None)
        display_name = kwargs.pop('display_name', None)
        metadata = kwargs.pop('metadata', {})
        location = kwargs.pop('location')
        user_id = kwargs.pop('user_id', ModuleStoreEnum.UserID.test)
        publish_item = kwargs.pop('publish_item', True)

        assert isinstance(location, UsageKey)
        assert location != parent_location

        store = kwargs.pop('modulestore')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = kwargs.pop('parent', None) or store.get_item(parent_location)

        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):

            if 'boilerplate' in kwargs:
                template_id = kwargs.pop('boilerplate')
                clz = XBlock.load_class(category, select=prefer_xmodules)
                template = clz.get_template(template_id)
                assert template is not None
                metadata.update(template.get('metadata', {}))
                if not isinstance(data, basestring):
                    data.update(template.get('data'))

            # replace the display name with an optional parameter passed in from the caller
            if display_name is not None:
                metadata['display_name'] = display_name

            module = store.create_child(
                user_id,
                parent.location,
                location.block_type,
                block_id=location.block_id,
                metadata=metadata,
                definition_data=data,
                runtime=parent.runtime,
                fields=kwargs,
            )

            # VS[compat] cdodge: This is a hack because static_tabs also have references from the course module, so
            # if we add one then we need to also add it to the policy information (i.e. metadata)
            # we should remove this once we can break this reference from the course to static tabs
            if category == 'static_tab':
                course = store.get_course(location.course_key)
                course.tabs.append(
                    StaticTab(
                        name=display_name,
                        url_slug=location.name,
                    )
                )
                store.update_item(course, user_id)

            # parent and publish the item, so it can be accessed
            if 'detached' not in module._class_tags:
                parent.children.append(location)
                store.update_item(parent, user_id)
                if publish_item:
                    published_parent = store.publish(parent.location, user_id)
                    # module is last child of parent
                    return published_parent.get_children()[-1]
                else:
                    return store.get_item(location)
            elif publish_item:
                return store.publish(location, user_id)
            else:
                return module


@contextmanager
def check_exact_number_of_calls(object_with_method, method_name, num_calls):
    """
    Instruments the given method on the given object to verify the number of calls to the
    method is exactly equal to 'num_calls'.
    """
    with check_number_of_calls(object_with_method, method_name, num_calls, num_calls):
        yield


def check_number_of_calls(object_with_method, method_name, maximum_calls, minimum_calls=1):
    """
    Instruments the given method on the given object to verify the number of calls to the method is
    less than or equal to the expected maximum_calls and greater than or equal to the expected minimum_calls.
    """
    return check_sum_of_calls(object_with_method, [method_name], maximum_calls, minimum_calls)


@contextmanager
def check_sum_of_calls(object_, methods, maximum_calls, minimum_calls=1):
    """
    Instruments the given methods on the given object to verify that the total sum of calls made to the
    methods falls between minumum_calls and maximum_calls.
    """
    mocks = {
        method: Mock(wraps=getattr(object_, method))
        for method in methods
    }

    with patch.multiple(object_, **mocks):
        yield

    call_count = sum(mock.call_count for mock in mocks.values())
    calls = pprint.pformat({
        method_name: mock.call_args_list
        for method_name, mock in mocks.items()
    })

    # Assertion errors don't handle multi-line values, so pretty-print to std-out instead
    if not minimum_calls <= call_count <= maximum_calls:
        print "Expected between {} and {} calls, {} were made. Calls: {}".format(
            minimum_calls,
            maximum_calls,
            call_count,
            calls,
        )

    # verify the counter actually worked by ensuring we have counted greater than (or equal to) the minimum calls
    assert_greater_equal(call_count, minimum_calls)

    # now verify the number of actual calls is less than (or equal to) the expected maximum
    assert_less_equal(call_count, maximum_calls)


def mongo_uses_error_check(store):
    """
    Does mongo use the error check as a separate message?
    """
    if hasattr(store, 'mongo_wire_version'):
        return store.mongo_wire_version() <= 1
    if hasattr(store, 'modulestores'):
        return any([mongo_uses_error_check(substore) for substore in store.modulestores])
    return False


@contextmanager
def check_mongo_calls(num_finds=0, num_sends=None):
    """
    Instruments the given store to count the number of calls to find (incl find_one) and the number
    of calls to send_message which is for insert, update, and remove (if you provide num_sends). At the
    end of the with statement, it compares the counts to the num_finds and num_sends.

    :param num_finds: the exact number of find calls expected
    :param num_sends: If none, don't instrument the send calls. If non-none, count and compare to
        the given int value.
    """
    with check_sum_of_calls(
            pymongo.message,
            ['query', 'get_more'],
            num_finds,
            num_finds
    ):
        if num_sends is not None:
            with check_sum_of_calls(
                    pymongo.message,
                    # mongo < 2.6 uses insert, update, delete and _do_batched_insert. >= 2.6 _do_batched_write
                    ['insert', 'update', 'delete', '_do_batched_write_command', '_do_batched_insert', ],
                    num_sends,
                    num_sends
            ):
                yield
        else:
            yield


# This dict represents the attribute keys for a course's 'about' info.
# Note: The 'video' attribute is intentionally excluded as it must be
# handled separately; its value maps to an alternate key name.
# Reference : cms/djangoapps/models/settings/course_details.py

ABOUT_ATTRIBUTES = {
    'effort': "Testing effort",
}


class CourseAboutFactory(XModuleFactory):
    """
    Factory for XModule course about.
    """

    @classmethod
    def _create(cls, target_class, **kwargs):  # pylint: disable=unused-argument
        """
        Uses **kwargs:

        effort:  effor information

        video : video link
        """
        user_id = kwargs.pop('user_id', None)
        course_id, course_runtime = kwargs.pop("course_id"), kwargs.pop("course_runtime")
        store = modulestore()
        for about_key in ABOUT_ATTRIBUTES:
            about_item = store.create_xblock(course_runtime, course_id, 'about', about_key)
            about_item.data = ABOUT_ATTRIBUTES[about_key]
            store.update_item(about_item, user_id, allow_not_found=True)
        about_item = store.create_xblock(course_runtime, course_id, 'about', 'video')
        about_item.data = "www.youtube.com/embed/testing-video-link"
        store.update_item(about_item, user_id, allow_not_found=True)
