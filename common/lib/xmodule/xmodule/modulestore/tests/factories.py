from factory import Factory, lazy_attribute_sequence, lazy_attribute
from uuid import uuid4
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.inheritance import own_metadata
from xmodule.x_module import ModuleSystem
from mitxmako.shortcuts import render_to_string
from xblock.runtime import InvalidScopeError
import datetime
from pytz import UTC


class XModuleCourseFactory(Factory):
    """
    Factory for XModule courses.
    """

    ABSTRACT_FACTORY = True

    @classmethod
    def _create(cls, target_class, *args, **kwargs):

        template = Location('i4x', 'edx', 'templates', 'course', 'Empty')
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
        new_course = store.clone_item(template, location)

        # This metadata code was copied from cms/djangoapps/contentstore/views.py
        if display_name is not None:
            new_course.display_name = display_name

        new_course.lms.start = datetime.datetime.now(UTC)
        new_course.tabs = kwargs.get(
            'tabs',
            [
                {"type": "courseware"},
                {"type": "course_info", "name": "Course Info"},
                {"type": "discussion", "name": "Discussion"},
                {"type": "wiki", "name": "Wiki"},
                {"type": "progress", "name": "Progress"}
            ]
        )
        new_course.discussion_link = kwargs.get('discussion_link')

        # Update the data in the mongo datastore
        store.update_metadata(new_course.location.url(), own_metadata(new_course))

        data = kwargs.get('data')
        if data is not None:
            store.update_item(new_course.location, data)

        return new_course


class Course:
    pass


class CourseFactory(XModuleCourseFactory):
    FACTORY_FOR = Course

    template = 'i4x://edx/templates/course/Empty'
    org = 'MITx'
    number = '999'
    display_name = 'Robot Super Course'


class XModuleItemFactory(Factory):
    """
    Factory for XModule items.
    """

    ABSTRACT_FACTORY = True

    display_name = None

    @lazy_attribute
    def category(attr):
        template = Location(attr.template)
        return template.category

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

        *template* (required): the template to create the item from
            (e.g. i4x://templates/section/Empty)

        *data* (optional): the data for the item
            (e.g. XML problem definition for a problem item)

        *display_name* (optional): the display name of the item

        *metadata* (optional): dictionary of metadata attributes

        *target_class* is ignored
        """

        DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']

        parent_location = Location(kwargs.get('parent_location'))
        template = Location(kwargs.get('template'))
        data = kwargs.get('data')
        display_name = kwargs.get('display_name')
        metadata = kwargs.get('metadata', {})

        store = modulestore('direct')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = store.get_item(parent_location)

        new_item = store.clone_item(template, kwargs.get('location'))

        # replace the display name with an optional parameter passed in from the caller
        if display_name is not None:
            new_item.display_name = display_name

        # Add additional metadata or override current metadata
        item_metadata = own_metadata(new_item)
        item_metadata.update(metadata)
        store.update_metadata(new_item.location.url(), item_metadata)

        # replace the data with the optional *data* parameter
        if data is not None:
            store.update_item(new_item.location, data)

        if new_item.location.category not in DETACHED_CATEGORIES:
            store.update_children(parent_location, parent.children + [new_item.location.url()])

        return new_item


class Item:
    pass


class ItemFactory(XModuleItemFactory):
    FACTORY_FOR = Item

    parent_location = 'i4x://MITx/999/course/Robot_Super_Course'
    template = 'i4x://edx/templates/chapter/Empty'

    @lazy_attribute_sequence
    def display_name(attr, n):
        return "{} {}".format(attr.category.title(), n)


def get_test_xmodule_for_descriptor(descriptor):
    """
    Attempts to create an xmodule which responds usually correctly from the descriptor. Not guaranteed.

    :param descriptor:
    """
    module_sys = ModuleSystem(
        ajax_url='',
        track_function=None,
        get_module=None,
        render_template=render_to_string,
        replace_urls=None,
        xblock_model_data=_test_xblock_model_data_accessor(descriptor)
    )
    return descriptor.xmodule(module_sys)

def _test_xblock_model_data_accessor(descriptor):
    simple_map = {}
    for field in descriptor.fields:
        try:
            simple_map[field.name] = getattr(descriptor, field.name)
        except InvalidScopeError:
            simple_map[field.name] = field.default
    for field in descriptor.module_class.fields:
        if field.name not in simple_map:
            simple_map[field.name] = field.default
    return lambda o: simple_map
