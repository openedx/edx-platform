"""
Django module for Course Metadata class -- manages advanced settings and related parameters
"""
from django.conf import settings
from django.utils.translation import ugettext as _
from six import text_type
from xblock.fields import Scope

from xblock_django.models import XBlockStudioConfigurationFlag
from xmodule.modulestore.django import modulestore


class CourseMetadata(object):
    '''
    For CRUD operations on metadata fields which do not have specific editors
    on the other pages including any user generated ones.
    The objects have no predefined attrs but instead are obj encodings of the
    editable metadata.
    '''
    # The list of fields that wouldn't be shown in Advanced Settings.
    # Should not be used directly. Instead the filtered_list method should
    # be used if the field needs to be filtered depending on the feature flag.
    FILTERED_LIST = [
        'cohort_config',
        'xml_attributes',
        'start',
        'end',
        'enrollment_start',
        'enrollment_end',
        'certificate_available_date',
        'tabs',
        'graceperiod',
        'show_timezone',
        'format',
        'graded',
        'hide_from_toc',
        'pdf_textbooks',
        'user_partitions',
        'name',  # from xblock
        'tags',  # from xblock
        'visible_to_staff_only',
        'group_access',
        'pre_requisite_courses',
        'entrance_exam_enabled',
        'entrance_exam_minimum_score_pct',
        'entrance_exam_id',
        'is_entrance_exam',
        'in_entrance_exam',
        'language',
        'certificates',
        'minimum_grade_credit',
        'default_time_limit_minutes',
        'is_proctored_enabled',
        'is_time_limited',
        'is_practice_exam',
        'exam_review_rules',
        'hide_after_due',
        'self_paced',
        'show_correctness',
        'chrome',
        'default_tab',
        'highlights_enabled_for_messaging',
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

        # Do not show edxnotes if the feature is disabled.
        if not settings.FEATURES.get('ENABLE_EDXNOTES'):
            filtered_list.append('edxnotes')

        # Do not show video auto advance if the feature is disabled
        if not settings.FEATURES.get('ENABLE_OTHER_COURSE_SETTINGS'):
            filtered_list.append('other_course_settings')

        # Do not show video_upload_pipeline if the feature is disabled.
        if not settings.FEATURES.get('ENABLE_VIDEO_UPLOAD_PIPELINE'):
            filtered_list.append('video_upload_pipeline')

        # Do not show video auto advance if the feature is disabled
        if not settings.FEATURES.get('ENABLE_AUTOADVANCE_VIDEOS'):
            filtered_list.append('video_auto_advance')

        # Do not show social sharing url field if the feature is disabled.
        if (not hasattr(settings, 'SOCIAL_SHARING_SETTINGS') or
                not getattr(settings, 'SOCIAL_SHARING_SETTINGS', {}).get("CUSTOM_COURSE_URLS")):
            filtered_list.append('social_sharing_url')

        # Do not show teams configuration if feature is disabled.
        if not settings.FEATURES.get('ENABLE_TEAMS'):
            filtered_list.append('teams_configuration')

        if not settings.FEATURES.get('ENABLE_VIDEO_BUMPER'):
            filtered_list.append('video_bumper')

        # Do not show enable_ccx if feature is not enabled.
        if not settings.FEATURES.get('CUSTOM_COURSES_EDX'):
            filtered_list.append('enable_ccx')
            filtered_list.append('ccx_connector')

        # Do not show "Issue Open Badges" in Studio Advanced Settings
        # if the feature is disabled.
        if not settings.FEATURES.get('ENABLE_OPENBADGES'):
            filtered_list.append('issue_badges')

        # If the XBlockStudioConfiguration table is not being used, there is no need to
        # display the "Allow Unsupported XBlocks" setting.
        if not XBlockStudioConfigurationFlag.is_enabled():
            filtered_list.append('allow_unsupported_xblocks')

        return filtered_list

    @classmethod
    def fetch(cls, descriptor):
        """
        Fetch the key:value editable course details for the given course from
        persistence and return a CourseMetadata model.
        """
        result = {}
        metadata = cls.fetch_all(descriptor)
        for key, value in metadata.iteritems():
            if key in cls.filtered_list():
                continue
            result[key] = value
        return result

    @classmethod
    def fetch_all(cls, descriptor):
        """
        Fetches all key:value pairs from persistence and returns a CourseMetadata model.
        """
        result = {}
        for field in descriptor.fields.values():
            if field.scope != Scope.settings:
                continue

            field_help = _(field.help)                  # pylint: disable=translation-of-non-string
            help_args = field.runtime_options.get('help_format_args')
            if help_args is not None:
                field_help = field_help.format(**help_args)

            result[field.name] = {
                'value': field.read_json(descriptor),
                'display_name': _(field.display_name),    # pylint: disable=translation-of-non-string
                'help': field_help,
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
                raise ValueError(_("Incorrect format for field '{name}'. {detailed_message}").format(
                    name=model['display_name'], detailed_message=text_type(err)))

        return cls.update_from_dict(key_values, descriptor, user)

    @classmethod
    def validate_and_update_from_json(cls, descriptor, jsondict, user, filter_tabs=True):
        """
        Validate the values in the json dict (validated by xblock fields from_json method)

        If all fields validate, go ahead and update those values on the object and return it without
        persisting it to the DB.
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
                errors.append({'message': text_type(err), 'model': model})

        # If did validate, go ahead and update the metadata
        if did_validate:
            updated_data = cls.update_from_dict(key_values, descriptor, user, save=False)

        return did_validate, errors, updated_data

    @classmethod
    def update_from_dict(cls, key_values, descriptor, user, save=True):
        """
        Update metadata descriptor from key_values. Saves to modulestore if save is true.
        """
        for key, value in key_values.iteritems():
            setattr(descriptor, key, value)

        if save and len(key_values):
            modulestore().update_item(descriptor, user.id)

        return cls.fetch(descriptor)
