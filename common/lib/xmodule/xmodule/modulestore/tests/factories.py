import datetime

from factory import Factory, lazy_attribute_sequence, lazy_attribute
from factory.containers import CyclicDefinitionError
from uuid import uuid4
from pytz import UTC

from xmodule.modulestore import Location
from xmodule.x_module import XModuleDescriptor


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
        # Delayed import so that we only depend on django if the caller
        # hasn't provided their own modulestore
        from xmodule.modulestore.django import editable_modulestore
        return editable_modulestore('direct')


class CourseFactory(XModuleFactory):
    """
    Factory for XModule courses.
    """
    org = 'MITx'
    number = '999'
    display_name = 'Robot Super Course'

    @classmethod
    def _create(cls, target_class, **kwargs):

        # All class attributes (from this class and base classes) are
        # passed in via **kwargs. However, some of those aren't actual field values,
        # so pop those off for use separately
        org = kwargs.pop('org', None)
        number = kwargs.pop('number', kwargs.pop('course', None))
        store = kwargs.pop('modulestore')

        location = Location('i4x', org, number, 'course', Location.clean(kwargs.get('display_name')))

        # Write the data to the mongo datastore
        new_course = store.create_xmodule(location, metadata=kwargs.get('metadata', None))

        new_course.start = datetime.datetime.now(UTC).replace(microsecond=0)

        # The rest of kwargs become attributes on the course:
        for k, v in kwargs.iteritems():
            setattr(new_course, k, v)

        # Update the data in the mongo datastore
        store.save_xmodule(new_course)
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

        return self.parent_location.replace(category=self.category, name=dest_name)

    @lazy_attribute
    def parent_location(self):
        default_location = Location('i4x://MITx/999/course/Robot_Super_Course')
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

        :target_class: is ignored
        """

        # All class attributes (from this class and base classes) are
        # passed in via **kwargs. However, some of those aren't actual field values,
        # so pop those off for use separately

        DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']
        # catch any old style users before they get into trouble
        assert 'template' not in kwargs
        parent_location = Location(kwargs.pop('parent_location', None))
        data = kwargs.pop('data', None)
        category = kwargs.pop('category', None)
        display_name = kwargs.pop('display_name', None)
        metadata = kwargs.pop('metadata', {})
        location = kwargs.pop('location')
        assert location != parent_location

        store = kwargs.pop('modulestore')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = kwargs.pop('parent', None) or store.get_item(parent_location)

        if 'boilerplate' in kwargs:
            template_id = kwargs.pop('boilerplate')
            clz = XModuleDescriptor.load_class(category)
            template = clz.get_template(template_id)
            assert template is not None
            metadata.update(template.get('metadata', {}))
            if not isinstance(data, basestring):
                data.update(template.get('data'))

        # replace the display name with an optional parameter passed in from the caller
        if display_name is not None:
            metadata['display_name'] = display_name
        module = store.create_and_save_xmodule(location, metadata=metadata, definition_data=data)

        module = store.get_item(location)

        for attr, val in kwargs.items():
            setattr(module, attr, val)
        module.save()

        store.save_xmodule(module)

        if location.category not in DETACHED_CATEGORIES:
            parent.children.append(location.url())
            store.update_children(parent_location, parent.children)

        return store.get_item(location)
