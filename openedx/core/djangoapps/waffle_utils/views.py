"""
Views that we will use to view toggle state in edx-platform.
"""
from collections import OrderedDict

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.permissions import IsStaff
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions, views
from rest_framework.response import Response
from waffle.models import Flag, Switch


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
        return Response(response)

    def _get_all_waffle_switches(self):
        """
        Gets all waffle switches and their state.
        """
        switches_dict = {}
        self._add_waffle_switch_state(switches_dict)
        switch_list = list(switches_dict.values())
        switch_list.sort(key=lambda toggle: toggle['name'])
        return switch_list

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

    def _get_all_waffle_flags(self):
        """
        Gets all waffle flags and their state.
        """
        flags_dict = {}
        self._add_waffle_flag_state(flags_dict)
        flag_list = list(flags_dict.values())
        flag_list.sort(key=lambda toggle: toggle['name'])
        return flag_list

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
