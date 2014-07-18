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
from nose.tools import assert_less_equal


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

        location = Location(org, number, run, 'course', name)

        with store.branch_setting(ModuleStoreEnum.Branch.draft_preferred):
            # Write the data to the mongo datastore
            new_course = store.create_xmodule(location, metadata=kwargs.get('metadata', None))

            # The rest of kwargs become attributes on the course:
            for k, v in kwargs.iteritems():
                setattr(new_course, k, v)

            # Save the attributes we just set
            new_course.save()
            # Update the data in the mongo datastore
            store.update_item(new_course, user_id)
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
            store.create_and_save_xmodule(location, user_id, metadata=metadata, definition_data=data, runtime=runtime)

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
def check_mongo_calls(mongo_store, max_finds=0, max_sends=None):
    """
    Instruments the given store to count the number of calls to find (incl find_one) and the number
    of calls to send_message which is for insert, update, and remove (if you provide max_sends). At the
    end of the with statement, it compares the counts to the max_finds and max_sends using a simple
    assertLessEqual.

    :param mongo_store: the MongoModulestore or subclass to watch
    :param max_finds: the maximum number of find calls to allow
    :param max_sends: If none, don't instrument the send calls. If non-none, count and compare to
        the given int value.
    """
    try:
        find_wrap = Mock(wraps=mongo_store.collection.find)
        wrap_patch = patch.object(mongo_store.collection, 'find', find_wrap)
        wrap_patch.start()
        if max_sends:
            sends_wrap = Mock(wraps=mongo_store.database.connection._send_message)
            sends_patch = patch.object(mongo_store.database.connection, '_send_message', sends_wrap)
            sends_patch.start()
        yield
    finally:
        wrap_patch.stop()
        if max_sends:
            sends_patch.stop()
            assert_less_equal(sends_wrap.call_count, max_sends)
        assert_less_equal(find_wrap.call_count, max_finds)
