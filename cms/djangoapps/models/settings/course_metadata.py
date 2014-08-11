from xblock.fields import Scope
from xmodule.modulestore.django import modulestore
from django.utils.translation import ugettext as _


class CourseMetadata(object):
    '''
    For CRUD operations on metadata fields which do not have specific editors
    on the other pages including any user generated ones.
    The objects have no predefined attrs but instead are obj encodings of the
    editable metadata.
    '''
    # The list of fields that wouldn't be shown in Advanced Settings.
    FILTERED_LIST = ['xml_attributes',
                     'start',
                     'end',
                     'enrollment_start',
                     'enrollment_end',
                     'tabs',
                     'graceperiod',
                     'checklists',
                     'show_timezone',
                     'format',
                     'graded',
                     'hide_from_toc',
                     'pdf_textbooks',
                     'name',  # from xblock
                     'tags',  # from xblock
                     'visible_to_staff_only'
    ]

    @classmethod
    def fetch(cls, descriptor):
        """
        Fetch the key:value editable course details for the given course from
        persistence and return a CourseMetadata model.
        """
        result = {}

        for field in descriptor.fields.values():
            if field.scope != Scope.settings:
                continue

            if field.name in cls.FILTERED_LIST:
                continue

            result[field.name] = {
                'value': field.read_json(descriptor),
                'display_name': _(field.display_name),
                'help': _(field.help),
                'deprecated': field.runtime_options.get('deprecated', False)
            }

        return result

    @classmethod
    def update_from_json(cls, descriptor, jsondict, user, filter_tabs=True):
        """
        Decode the json into CourseMetadata and save any changed attrs to the db.

        Ensures none of the fields are in the blacklist.
        """
        # Copy the filtered list to avoid permanently changing the class attribute.
        filtered_list = list(cls.FILTERED_LIST)
        # Don't filter on the tab attribute if filter_tabs is False.
        if not filter_tabs:
            filtered_list.remove("tabs")

        # Validate the values before actually setting them.
        key_values = {}

        for key, model in jsondict.iteritems():
            # should it be an error if one of the filtered list items is in the payload?
            if key in filtered_list:
                continue
            try:
                val = model['value']
                if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                    key_values[key] = descriptor.fields[key].from_json(val)
            except (TypeError, ValueError) as err:
                raise ValueError(_("Incorrect format for field '{name}'. {detailed_message}".format(
                    name=model['display_name'], detailed_message=err.message)))

        for key, value in key_values.iteritems():
            setattr(descriptor, key, value)

        if len(key_values) > 0:
            modulestore().update_item(descriptor, user.id)

        return cls.fetch(descriptor)
