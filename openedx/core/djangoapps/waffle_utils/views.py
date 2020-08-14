"""
Views that we will use to view toggle state in edx-platform.
"""
from collections import OrderedDict
from django.conf import settings

from edx_django_utils.monitoring.code_owner.utils import get_code_owner_from_module, is_code_owner_mappings_configured
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.permissions import IsStaff
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions, views
from rest_framework.response import Response
from waffle.models import Flag, Switch

from . import WaffleFlag, WaffleSwitch
from .models import WaffleFlagCourseOverrideModel


class ToggleStateView(views.APIView):
    """
    An endpoint for displaying the state of toggles in edx-platform.
    """
    authentication_classes = (JwtAuthentication, SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated, IsStaff,)

    def get(self, request):
        response = OrderedDict()
        response['waffle_flags'] = self._get_all_waffle_flags()
        response['waffle_switches'] = self._get_all_waffle_switches()
        response['django_settings'] = self._get_settings_state()
        return Response(response)

    def _get_all_waffle_switches(self):
        """
        Gets all waffle switches and their state.
        """
        switches_dict = {}
        self._add_waffle_switch_instances(switches_dict)
        self._add_waffle_switch_state(switches_dict)
        self._add_waffle_switch_computed_status(switches_dict)
        switch_list = list(switches_dict.values())
        switch_list.sort(key=lambda toggle: toggle['name'])
        return switch_list

    def _add_waffle_switch_instances(self, switches_dict):
        """
        Add details from waffle switch instances, like code_owner.
        """
        waffle_switch_instances = WaffleSwitch.get_instances()
        for switch_instance in waffle_switch_instances:
            switch_name = switch_instance.namespaced_switch_name
            switch = self._get_or_create_toggle_response(switches_dict, switch_name)
            self._add_toggle_instance_details(switch, switch_instance)

    def _add_waffle_switch_state(self, switches_dict):
        """
        Add waffle switch state from the waffle Switch model.
        """
        waffle_switches = Switch.objects.all()
        for switch_data in waffle_switches:
            switch = self._get_or_create_toggle_response(switches_dict, switch_data.name)
            switch['is_active'] = 'true' if switch_data.active else 'false'
            if switch_data.note:
                switch['note'] = switch_data.note
            switch['created'] = str(switch_data.created)
            switch['modified'] = str(switch_data.modified)

    def _add_waffle_switch_computed_status(self, switch_dict):
        """
        Add computed status to each waffle switch.
        """
        for switch in switch_dict.values():
            computed_status = 'off'
            if 'is_active' in switch:
                if switch['is_active'] == 'true':
                    computed_status = 'on'
                else:
                    computed_status = 'off'
            switch['computed_status'] = computed_status

    def _get_all_waffle_flags(self):
        """
        Gets all waffle flags and their state.
        """
        flags_dict = {}
        self._add_waffle_flag_instances(flags_dict)
        self._add_waffle_flag_state(flags_dict)
        self._add_waffle_flag_course_override_state(flags_dict)
        self._add_waffle_flag_computed_status(flags_dict)
        flag_list = list(flags_dict.values())
        flag_list.sort(key=lambda toggle: toggle['name'])
        return flag_list

    def _add_waffle_flag_instances(self, flags_dict):
        """
        Add details from waffle flag instances, like code_owner.
        """
        waffle_flag_instances = WaffleFlag.get_instances()
        for flag_instance in waffle_flag_instances:
            flag_name = flag_instance.namespaced_flag_name
            flag = self._get_or_create_toggle_response(flags_dict, flag_name)
            self._add_toggle_instance_details(flag, flag_instance)

    def _add_toggle_instance_details(self, toggle, toggle_instance):
        """
        Add details (class, module, code_owner) from a specific toggle instance.
        """
        toggle['class'] = toggle_instance.__class__.__name__
        toggle['module'] = toggle_instance.module_name
        if is_code_owner_mappings_configured():
            code_owner = get_code_owner_from_module(toggle_instance.module_name)
            if code_owner:
                toggle['code_owner'] = code_owner

    def _add_waffle_flag_state(self, flags_dict):
        """
        Add waffle flag state from the waffle Flag model.
        """
        waffle_flags = Flag.objects.all()
        for flag_data in waffle_flags:
            flag = self._get_or_create_toggle_response(flags_dict, flag_data.name)
            if flag_data.everyone is True:
                everyone = 'yes'
            elif flag_data.everyone is False:
                everyone = 'no'
            else:
                everyone = 'unknown'
            flag['everyone'] = everyone
            if flag_data.note:
                flag['note'] = flag_data.note
            flag['created'] = str(flag_data.created)
            flag['modified'] = str(flag_data.modified)

    def _add_waffle_flag_course_override_state(self, flags_dict):
        """
        Add waffle flag course override state from the WaffleFlagCourseOverrideModel model.
        """
        # This dict is keyed by flag name, and contains dicts keyed by course_id, the contains
        # the final dict of metadata for a single course override that will be returned.
        flag_course_overrides = OrderedDict()
        # Note: We can't just get enabled records, because if a historical record is enabled but
        #   the current record is disabled, we would not know this. We get all records, and mark
        #   some overrides as disabled, and then later filter the disabled records.
        course_overrides_data = WaffleFlagCourseOverrideModel.objects.all()
        course_overrides_data = course_overrides_data.order_by('waffle_flag', 'course_id', '-change_date')
        for course_override_data in course_overrides_data:
            flag_name = course_override_data.waffle_flag
            course_id = str(course_override_data.course_id)
            if flag_name not in flag_course_overrides:
                flag_course_overrides[flag_name] = OrderedDict()
            course_overrides = flag_course_overrides[flag_name]
            if course_id not in course_overrides:
                course_overrides[course_id] = OrderedDict()
            course_override = course_overrides[course_id]
            # data is reverse ordered by date, so the first record is the current record
            if 'course_id' not in course_override:
                course_override['course_id'] = course_id
                if not course_override_data.enabled:
                    # The current record may be disabled, but later history might be enabled.
                    # We'll filter these disabled records below.
                    course_override['disabled'] = True
                else:
                    course_override['force'] = course_override_data.override_choice
                    course_override['modified'] = str(course_override_data.change_date)
            # data is reverse ordered by date, so the last record is the oldest record
            course_override['created'] = str(course_override_data.change_date)

        for flag_name, course_overrides_dict in flag_course_overrides.items():
            course_overrides = [
                course_override for course_override in course_overrides_dict.values()
                if 'disabled' not in course_override
            ]
            if course_overrides:
                flag = self._get_or_create_toggle_response(flags_dict, flag_name)
                flag['course_overrides'] = course_overrides

    def _add_waffle_flag_computed_status(self, flags_dict):
        """
        Add computed status to each waffle flag.
        """
        for flag in flags_dict.values():
            computed_status = 'off'
            if 'everyone' in flag:
                if flag['everyone'] == 'yes':
                    computed_status = 'on'
                elif flag['everyone'] == 'unknown':
                    computed_status = 'both'
            # check course overrides only if computed_status is not already 'both'
            if computed_status != 'both' and 'course_overrides' in flag:
                has_force_on = any(override['force'] == 'on' for override in flag['course_overrides'])
                has_force_off = any(override['force'] == 'off' for override in flag['course_overrides'])
                if has_force_on and has_force_off:
                    computed_status = 'both'
                elif has_force_on:
                    computed_status = 'on' if computed_status == 'on' else 'both'
                elif has_force_off:
                    computed_status = 'off' if computed_status == 'off' else 'both'
            flag['computed_status'] = computed_status

    def _get_or_create_toggle_response(self, toggles_dict, toggle_name):
        """
        Gets or creates a toggle response dict and adds it to the toggles_dict.

        Returns:
            Either the pre-existing toggle response, or a new toggle dict with its name set.

        """
        if toggle_name in toggles_dict:
            return toggles_dict[toggle_name]
        toggle = OrderedDict()
        toggle['name'] = toggle_name
        toggles_dict[toggle_name] = toggle
        return toggle

    def _get_settings_state(self):
        """
        Returns a dictionary of settings values. Will only return values that are set to true or false.
        """

        bool_settings = list()
        for setting_name, setting_value in vars(settings).items():
            if isinstance(setting_value, dict):
                for dict_name, dict_value in setting_value.items():
                    if isinstance(dict_value, bool):
                        bool_settings.append(
                            {
                                'name': "{setting_name}['{dict_name}']".format(setting_name=setting_name, dict_name=dict_name),
                                'is_active': dict_value,
                            }
                        )
            elif isinstance(setting_value, bool):
                bool_settings.append({'name': setting_name, 'is_active': setting_value})
        return bool_settings
