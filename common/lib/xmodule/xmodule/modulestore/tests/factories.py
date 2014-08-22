from factory import Factory, lazy_attribute_sequence, lazy_attribute
from factory.containers import CyclicDefinitionError
from uuid import uuid4

from xmodule.modulestore import prefer_xmodules, ModuleStoreEnum
from opaque_keys.edx.locations import Location, SlashSeparatedCourseKey
from opaque_keys.edx.keys import UsageKey
from xblock.core import XBlock
from xmodule.tabs import StaticTab
from decorator import contextmanager
from mock import Mock, patch
from nose.tools import assert_less_equal, assert_greater_equal, assert_equal


class Dummy(object):
    pass


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
        from xmodule.modulestore.django import modulestore
        return modulestore()


class CourseFactory(XModuleFactory):
    """
    Factory for XModule courses.
    """
    org = 'MITx'
    number = '999'
    display_name = 'Robot Super Course'

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
        run = kwargs.get('run', name)
        user_id = kwargs.pop('user_id', ModuleStoreEnum.UserID.test)

        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            # Write the data to the mongo datastore
            kwargs.update(kwargs.get('metadata', {}))
            course_key = SlashSeparatedCourseKey(org, number, run)
            # TODO - We really should call create_course here.  However, since create_course verifies there are no
            # duplicates, this breaks several tests that do not clean up properly in between tests.
            new_course = store.create_xblock(None, course_key, 'course', block_id=run, fields=kwargs)
            store.update_item(new_course, user_id, allow_not_found=True)
            return new_course


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
        default_location = Location('MITx', '999', 'Robot_Super_Course', 'course', 'Robot_Super_Course', None)
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
            runtime = parent.runtime if parent else None
            store.create_item(
                user_id,
                location.course_key,
                location.block_type,
                block_id=location.block_id,
                metadata=metadata,
                definition_data=data,
                runtime=runtime
            )

            module = store.get_item(location)

            for attr, val in kwargs.items():
                setattr(module, attr, val)
            # Save the attributes we just set
            module.save()

            store.update_item(module, user_id)

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
                    store.publish(parent.location, user_id)
            elif publish_item:
                store.publish(location, user_id)

        # return the published item
        return store.get_item(location)


@contextmanager
def check_exact_number_of_calls(object_with_method, method, num_calls, method_name=None):
    """
    Instruments the given method on the given object to verify the number of calls to the
    method is exactly equal to 'num_calls'.
    """
    with check_number_of_calls(object_with_method, method, num_calls, num_calls, method_name):
        yield


@contextmanager
def check_number_of_calls(object_with_method, method, maximum_calls, minimum_calls=1, method_name=None):
    """
    Instruments the given method on the given object to verify the number of calls to the method is
    less than or equal to the expected maximum_calls and greater than or equal to the expected minimum_calls.
    """
    method_wrap = Mock(wraps=method)
    wrap_patch = patch.object(object_with_method, method_name or method.__name__, method_wrap)

    try:
        wrap_patch.start()
        yield

    finally:
        wrap_patch.stop()

        # verify the counter actually worked by ensuring we have counted greater than (or equal to) the minimum calls
        assert_greater_equal(method_wrap.call_count, minimum_calls)

        # now verify the number of actual calls is less than (or equal to) the expected maximum
        assert_less_equal(method_wrap.call_count, maximum_calls)


@contextmanager
def check_mongo_calls(mongo_store, num_finds=0, num_sends=None):
    """
    Instruments the given store to count the number of calls to find (incl find_one) and the number
    of calls to send_message which is for insert, update, and remove (if you provide num_sends). At the
    end of the with statement, it compares the counts to the num_finds and num_sends.

    :param mongo_store: the MongoModulestore or subclass to watch or a SplitMongoModuleStore
    :param num_finds: the exact number of find calls expected
    :param num_sends: If none, don't instrument the send calls. If non-none, count and compare to
        the given int value.
    """
    if mongo_store.get_modulestore_type() == ModuleStoreEnum.Type.mongo:
        with check_exact_number_of_calls(mongo_store.collection, mongo_store.collection.find, num_finds):
            if num_sends is not None:
                with check_exact_number_of_calls(
                    mongo_store.database.connection,
                    mongo_store.database.connection._send_message,  # pylint: disable=protected-access
                    num_sends,
                ):
                    yield
            else:
                yield
    elif mongo_store.get_modulestore_type() == ModuleStoreEnum.Type.split:
        collections = [
            mongo_store.db_connection.course_index,
            mongo_store.db_connection.structures,
            mongo_store.db_connection.definitions,
        ]
        # could add else clause which raises exception or just rely on the below to suss that out
        try:
            find_wraps = []
            wrap_patches = []
            for collection in collections:
                find_wrap = Mock(wraps=collection.find)
                find_wraps.append(find_wrap)
                wrap_patch = patch.object(collection, 'find', find_wrap)
                wrap_patches.append(wrap_patch)
                wrap_patch.start()
            if num_sends is not None:
                connection = mongo_store.db_connection.database.connection
                with check_exact_number_of_calls(
                    connection,
                    connection._send_message,  # pylint: disable=protected-access
                    num_sends,
                ):
                    yield
            else:
                yield
        finally:
            map(lambda wrap_patch: wrap_patch.stop(), wrap_patches)
            call_count = sum([find_wrap.call_count for find_wrap in find_wraps])
            assert_equal(call_count, num_finds)
