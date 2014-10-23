from xblock.fields import Scope
from xmodule.modulestore.django import modulestore
from django.utils.translation import ugettext as _
from django.conf import settings


class CourseMetadata(object):
    '''
    For CRUD operations on metadata fields which do not have specific editors
    on the other pages including any user generated ones.
    The objects have no predefined attrs but instead are obj encodings of the
    editable metadata.
    '''
    # The list of fields that wouldn't be shown in Advanced Settings.
    # Should not be used directly. Instead the filtered_list method should be used if the field needs to be filtered
    # depending on the feature flag.
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
    def filtered_list(cls):
        """
        Filter fields based on feature flag, i.e. enabled, disabled.
        """
        # Copy the filtered list to avoid permanently changing the class attribute.
        filtered_list = list(cls.FILTERED_LIST)

        # Do not show giturl if feature is not enabled.
        if not settings.FEATURES.get('ENABLE_EXPORT_GIT'):
            filtered_list.append('giturl')

        return filtered_list

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

            if field.name in cls.filtered_list():
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
        filtered_list = cls.filtered_list()
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

        return cls.update_from_dict(key_values, descriptor, user)

    @classmethod
    def validate_and_update_from_json(cls, descriptor, jsondict, user, filter_tabs=True):
        """
        Validate the values in the json dict (validated by xblock fields from_json method)

        If all fields validate, go ahead and update those values in the database.
        If not, return the error objects list.

        Returns:
            did_validate: whether values pass validation or not
            errors: list of error objects
            result: the updated course metadata or None if error
        """
        filtered_list = cls.filtered_list()
        if not filter_tabs:
            filtered_list.remove("tabs")

        filtered_dict = dict((k, v) for k, v in jsondict.iteritems() if k not in filtered_list)
        did_validate = True
        errors = []
        key_values = {}
        updated_data = None

        for key, model in filtered_dict.iteritems():
            try:
                val = model['value']
                if hasattr(descriptor, key) and getattr(descriptor, key) != val:
                    key_values[key] = descriptor.fields[key].from_json(val)
            except (TypeError, ValueError) as err:
                did_validate = False
                errors.append({'message': err.message, 'model': model})

        # If did validate, go ahead and update the metadata
        if did_validate:
            updated_data = cls.update_from_dict(key_values, descriptor, user)

        return did_validate, errors, updated_data

    @classmethod
    def update_from_dict(cls, key_values, descriptor, user):
        """
        Update metadata descriptor in modulestore from key_values.
        """
        for key, value in key_values.iteritems():
            setattr(descriptor, key, value)

        if len(key_values):
            modulestore().update_item(descriptor, user.id)

        return cls.fetch(descriptor)
