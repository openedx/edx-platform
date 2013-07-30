import datetime

from factory import Factory, LazyAttributeSequence
from uuid import uuid4
from pytz import UTC

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from xblock.core import Scope
from xmodule.x_module import XModuleDescriptor

class XModuleCourseFactory(Factory):
    """
    Factory for XModule courses.
    """

    ABSTRACT_FACTORY = True

    @classmethod
    def _create(cls, target_class, **kwargs):

        org = kwargs.pop('org', None)
        number = kwargs.pop('number', kwargs.pop('course', None))
        display_name = kwargs.pop('display_name', None)
        location = Location('i4x', org, number, 'course', Location.clean(display_name))

        try:
            store = modulestore('direct')
        except KeyError:
            store = modulestore()

        # Write the data to the mongo datastore
        new_course = store.create_xmodule(location)

        # This metadata code was copied from cms/djangoapps/contentstore/views.py
        if display_name is not None:
            new_course.display_name = display_name

        new_course.lms.start = datetime.datetime.now(UTC).replace(microsecond=0)

        # The rest of kwargs become attributes on the course:
        for k, v in kwargs.iteritems():
            setattr(new_course, k, v)

        # Update the data in the mongo datastore
        store.save_xmodule(new_course)
        return new_course


class Course:
    pass


class CourseFactory(XModuleCourseFactory):
    FACTORY_FOR = Course

    org = 'MITx'
    number = '999'
    display_name = 'Robot Super Course'


class XModuleItemFactory(Factory):
    """
    Factory for XModule items.
    """

    ABSTRACT_FACTORY = True

    parent_location = 'i4x://MITx/999/course/Robot_Super_Course'
    category = 'problem'
    display_name = LazyAttributeSequence(lambda o, n: "{} {}".format(o.category, n))

    @staticmethod
    def location(parent, category, display_name):
        dest_name = display_name.replace(" ", "_") if display_name is not None else uuid4().hex
        return Location(parent).replace(category=category, name=dest_name)

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

        DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']
        # catch any old style users before they get into trouble
        assert not 'template' in kwargs
        parent_location = Location(kwargs.get('parent_location'))
        data = kwargs.get('data')
        category = kwargs.get('category')
        display_name = kwargs.get('display_name')
        metadata = kwargs.get('metadata', {})
        location = kwargs.get('location', XModuleItemFactory.location(parent_location, category, display_name))
        assert location != parent_location
        if kwargs.get('boilerplate') is not None:
            template_id = kwargs.get('boilerplate')
            clz = XModuleDescriptor.load_class(category)
            template = clz.get_template(template_id)
            assert template is not None
            metadata.update(template.get('metadata', {}))
            if not isinstance(data, basestring):
                data.update(template.get('data'))

        store = modulestore('direct')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = store.get_item(parent_location)

        # replace the display name with an optional parameter passed in from the caller
        if display_name is not None:
            metadata['display_name'] = display_name
        store.create_and_save_xmodule(location, metadata=metadata, definition_data=data)

        if location.category not in DETACHED_CATEGORIES:
            parent.children.append(location.url())
            store.update_children(parent_location, parent.children)

        return store.get_item(location)


class Item:
    pass


class ItemFactory(XModuleItemFactory):
    FACTORY_FOR = Item
    category = 'chapter'
