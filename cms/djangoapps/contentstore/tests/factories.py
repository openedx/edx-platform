from factory import Factory
from datetime import datetime
from uuid import uuid4
from student.models import (User, UserProfile, Registration,
                            CourseEnrollmentAllowed)
from django.contrib.auth.models import Group

from django.contrib.auth.models import Group

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.timeparse import stringify_time
from student.models import (User, UserProfile, Registration,
                            CourseEnrollmentAllowed)
from django.contrib.auth.models import Group

class UserProfileFactory(Factory):
    FACTORY_FOR = UserProfile

    user = None
    name = 'Robot Studio'
    courseware = 'course.xml'


class RegistrationFactory(Factory):
    FACTORY_FOR = Registration

    user = None
    activation_key = uuid4().hex


class UserFactory(Factory):
    FACTORY_FOR = User

    username = 'robot'
    email = 'robot@edx.org'
    password = 'test'
    first_name = 'Robot'
    last_name = 'Tester'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime.now()
    date_joined = datetime.now()


class GroupFactory(Factory):
    FACTORY_FOR = Group

    name = 'test_group'


class CourseEnrollmentAllowedFactory(Factory):
    FACTORY_FOR = CourseEnrollmentAllowed

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
    _creation_function = (XMODULE_ITEM_CREATION,)

    @classmethod
    def _create(cls, target_class, *args, **kwargs):
        """
        kwargs must include parent_location, template. Can contain display_name
        target_class is ignored
        """

        DETACHED_CATEGORIES = ['about', 'static_tab', 'course_info']
        
        parent_location = Location(kwargs.get('parent_location'))
        template = Location(kwargs.get('template'))
        display_name = kwargs.get('display_name')

        store = modulestore('direct')

        # This code was based off that in cms/djangoapps/contentstore/views.py
        parent = store.get_item(parent_location)
        dest_location = parent_location._replace(category=template.category, name=uuid4().hex)

        new_item = store.clone_item(template, dest_location)

        # TODO: This needs to be deleted when we have proper storage for static content
        new_item.metadata['data_dir'] = parent.metadata['data_dir']

        # replace the display name with an optional parameter passed in from the caller
        if display_name is not None:
            new_item.metadata['display_name'] = display_name

        store.update_metadata(new_item.location.url(), new_item.own_metadata)

        if new_item.location.category not in DETACHED_CATEGORIES:
            store.update_children(parent_location, parent.definition.get('children', []) + [new_item.location.url()])

        return new_item

class Item:
    pass

class ItemFactory(XModuleItemFactory):
    FACTORY_FOR = Item

    parent_location = 'i4x://MITx/999/course/Robot_Super_Course'
    template = 'i4x://edx/templates/chapter/Empty'
    display_name = 'Section One'

class UserProfileFactory(Factory):
    FACTORY_FOR = UserProfile

    user = None
    name = 'Robot Studio'
    courseware = 'course.xml'

class RegistrationFactory(Factory):
    FACTORY_FOR = Registration

    user = None
    activation_key = uuid.uuid4().hex

class UserFactory(Factory):
    FACTORY_FOR = User

    username = 'robot'
    email = 'robot@edx.org'
    password = 'test'
    first_name = 'Robot'
    last_name = 'Tester'
    is_staff = False
    is_active = True
    is_superuser = False
    last_login = datetime.now()
    date_joined = datetime.now()

class GroupFactory(Factory):
    FACTORY_FOR = Group

    name = 'test_group'

class CourseEnrollmentAllowedFactory(Factory):
    FACTORY_FOR = CourseEnrollmentAllowed
