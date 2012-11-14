from factory import Factory
from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from time import gmtime
from uuid import uuid4
from xmodule.timeparse import stringify_time


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

        store = modulestore('direct')

        # Write the data to the mongo datastore
        new_course = store.clone_item(template, location)

        # This metadata code was copied from cms/djangoapps/contentstore/views.py
        if display_name is not None:
            new_course.metadata['display_name'] = display_name

        new_course.metadata['data_dir'] = uuid4().hex
        new_course.metadata['start'] = stringify_time(gmtime())
        new_course.tabs = [{"type": "courseware"}, 
            {"type": "course_info", "name": "Course Info"}, 
            {"type": "discussion", "name": "Discussion"},
            {"type": "wiki", "name": "Wiki"},
            {"type": "progress", "name": "Progress"}]

        # Update the data in the mongo datastore
        store.update_metadata(new_course.location.url(), new_course.own_metadata)   

        return new_course

class Course:
    pass

class CourseFactory(XModuleCourseFactory):
    FACTORY_FOR = Course

    template = 'i4x://edx/templates/course/Empty'
    org = 'MITx'
    number = '999'
    display_name = 'Robot Super Course'