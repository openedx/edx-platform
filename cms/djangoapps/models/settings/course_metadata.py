from xmodule.modulestore import Location
from contentstore.utils import get_modulestore
from xmodule.modulestore.inheritance import own_metadata
from xblock.fields import Scope
from cms.xmodule_namespace import CmsBlockMixin


class CourseMetadata(object):
    '''
    For CRUD operations on metadata fields which do not have specific editors
    on the other pages including any user generated ones.
    The objects have no predefined attrs but instead are obj encodings of the
    editable metadata.
    '''
    FILTERED_LIST = ['xml_attributes',
                     'start',
                     'end',
                     'enrollment_start',
                     'enrollment_end',
                     'tabs',
                     'graceperiod',
                     'checklists',
                     'show_timezone'
    ]

    @classmethod
    def fetch(cls, course_location):
        """
        Fetch the key:value editable course details for the given course from
        persistence and return a CourseMetadata model.
        """
        if not isinstance(course_location, Location):
            course_location = Location(course_location)

        course = {}

        descriptor = get_modulestore(course_location).get_item(course_location)

        for field in descriptor.fields.values():
            if field.name in CmsBlockMixin.fields:
                continue

            if field.scope != Scope.settings:
                continue

            if field.name in cls.FILTERED_LIST:
                continue

            course[field.name] = field.read_json(descriptor)

        return course

    @classmethod
    def update_from_json(cls, course_location, jsondict, filter_tabs=True):
        """
        Decode the json into CourseMetadata and save any changed attrs to the db.

        Ensures none of the fields are in the blacklist.
        """
        descriptor = get_modulestore(course_location).get_item(course_location)

        dirty = False

        # Copy the filtered list to avoid permanently changing the class attribute.
        filtered_list = list(cls.FILTERED_LIST)
        # Don't filter on the tab attribute if filter_tabs is False.
        if not filter_tabs:
            filtered_list.remove("tabs")

        for key, val in jsondict.iteritems():
            # should it be an error if one of the filtered list items is in the payload?
            if key in filtered_list:
                continue

            if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                dirty = True
                value = descriptor.fields[key].from_json(val)
                setattr(descriptor, key, value)

        if dirty:
            # Save the data that we've just changed to the underlying
            # MongoKeyValueStore before we update the mongo datastore.
            descriptor.save()
            get_modulestore(course_location).update_metadata(course_location,
                                                             own_metadata(descriptor))

        # Could just generate and return a course obj w/o doing any db reads,
        # but I put the reads in as a means to confirm it persisted correctly
        return cls.fetch(course_location)

    @classmethod
    def delete_key(cls, course_location, payload):
        '''
        Remove the given metadata key(s) from the course. payload can be a
        single key or [key..]
        '''
        descriptor = get_modulestore(course_location).get_item(course_location)

        for key in payload['deleteKeys']:
            if hasattr(descriptor, key):
                delattr(descriptor, key)

        # Save the data that we've just changed to the underlying
        # MongoKeyValueStore before we update the mongo datastore.
        descriptor.save()

        get_modulestore(course_location).update_metadata(course_location,
                                                         own_metadata(descriptor))

        return cls.fetch(course_location)
