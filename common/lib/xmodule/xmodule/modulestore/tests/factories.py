from factory import Factory, lazy_attribute_sequence, lazy_attribute
from time import gmtime
from uuid import uuid4
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.timeparse import stringify_time
from xmodule.modulestore.inheritance import own_metadata


class XModuleCourseFactory(Factory):
    """
    Factory for XModule courses.
    """

    ABSTRACT_FACTORY = True

    @classmethod
    def _create(cls, target_class, *args, **kwargs):

        org = kwargs.get('org')
        number = kwargs.get('number')
        display_name = kwargs.get('display_name')
        location = Location('i4x', org, number,
                            'course', Location.clean(display_name))

        try:
            store = modulestore('direct')
        except KeyError:
            store = modulestore()

        # Write the data to the mongo datastore
        if display_name is None:
            metadata = {}
        else:
            metadata = {'display_name': display_name}
        new_course = store.create_and_save_xmodule(location, metadata=metadata, definition_data=kwargs.get('data'))

        # clone a default 'about' module as well
        dest_about_location = location._replace(category='about', name='overview')
        store.create_and_save_xmodule(dest_about_location, system=new_course.system)

        # NOTE: these factories in general aren't really valid tests as this hardcoding shows.
        new_course.discussion_link = kwargs.get('discussion_link')
        new_course.tabs = kwargs.get('tabs',
            [{"type": "courseware"},
                {"type": "course_info", "name": "Course Info"},
                {"type": "discussion", "name": "Discussion"},
                {"type": "wiki", "name": "Wiki"},
                {"type": "progress", "name": "Progress"}])

        store.update_metadata(new_course.location.url(), own_metadata(new_course))

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

    display_name = None
    category = 'problem'

    @lazy_attribute
    def location(attr):
        parent = Location(attr.parent_location)
        dest_name = attr.display_name.replace(" ", "_") if attr.display_name is not None else uuid4().hex
        return parent._replace(category=attr.category, name=dest_name)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        """
        Uses *kwargs*:

        *parent_location* (required): the location of the parent module
            (e.g. the parent course or section)

        category: the category of the resulting item.

        *data* (optional): the data for the item
            (e.g. XML problem definition for a problem item)

        *display_name* (optional): the display name of the item

        *metadata* (optional): dictionary of metadata attributes

        *target_class* is ignored
        """

        DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']

        parent_location = Location(kwargs.get('parent_location'))
        data = kwargs.get('data')
        display_name = kwargs.get('display_name')
        metadata = kwargs.get('metadata', {})

        store = modulestore('direct')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = store.get_item(parent_location)

        # replace the display name with an optional parameter passed in from the caller
        if display_name is not None:
            metadata['display_name'] = display_name
        new_item = store.create_and_save_xmodule(kwargs.get('location'), metadata=metadata, definition_data=data)

        if new_item.location.category not in DETACHED_CATEGORIES:
            store.update_children(parent_location, parent.children + [new_item.location.url()])

        return new_item


class Item:
    pass


class ItemFactory(XModuleItemFactory):
    FACTORY_FOR = Item

    parent_location = 'i4x://MITx/999/course/Robot_Super_Course'
    category = 'chapter'

    @lazy_attribute_sequence
    def display_name(attr, n):
        return "{} {}".format(attr.category.title(), n)
