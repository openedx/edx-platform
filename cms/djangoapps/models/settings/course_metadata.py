from xblock.fields import Scope

from contentstore.utils import get_modulestore
from xmodule.modulestore.inheritance import own_metadata
from cms.lib.xblock.mixin import CmsBlockMixin


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
                     'graceperiod',
                     'checklists',
                     'show_timezone',
                     'format',
                     'graded',
    ]

    @classmethod
    def fetch(cls, descriptor):
        """
        Fetch the key:value editable course details for the given course from
        persistence and return a CourseMetadata model.
        """
        result = {}

        for field in descriptor.fields.values():
            if field.name in CmsBlockMixin.fields:
                continue

            if field.scope != Scope.settings:
                continue

            if field.name in cls.FILTERED_LIST:
                continue

            result[field.name] = field.read_json(descriptor)

        return result

    @classmethod
    def update_from_json(cls, descriptor, jsondict):
        """
        Decode the json into CourseMetadata and save any changed attrs to the db.

        Ensures none of the fields are in the blacklist.
        """
        dirty = False

        # Copy the filtered list to avoid permanently changing the class attribute.
        filtered_list = list(cls.FILTERED_LIST)

        for key, val in jsondict.iteritems():
            # should it be an error if one of the filtered list items is in the payload?
            if key in filtered_list:
                continue

            if key == "unsetKeys":
                dirty = True
                for unset in val:
                    descriptor.fields[unset].delete_from(descriptor)

            if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                dirty = True
                value = descriptor.fields[key].from_json(val)
                setattr(descriptor, key, value)

        if dirty:
            get_modulestore(descriptor.location).update_metadata(descriptor.location, own_metadata(descriptor))

        return cls.fetch(descriptor)
