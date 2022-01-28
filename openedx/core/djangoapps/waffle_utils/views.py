"""
Views that we will use to view toggle state in edx-platform.
"""
from collections import OrderedDict
from enum import Enum

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.permissions import IsStaff
from edx_toggles.toggles.state import ToggleStateReport, get_or_create_toggle_response
from rest_framework import views
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from .models import WaffleFlagCourseOverrideModel, WaffleFlagOrgOverrideModel


class OverrideToggleStateReport(ToggleStateReport):
    """
    Override some of the methods from ToggleStateReport to expose toggles from both the
    WaffleFlagCourseOverrideModel and WaffleFlagOrgOverrideModel objects.
    """

    def add_waffle_flag_instances(self, flags_dict):
        """
        Append objects from WaffleFlagCourseOverrideModel and WaffleFlagOrgOverrideModel.
        """
        super().add_waffle_flag_state(flags_dict)
        _add_waffle_flag_override_states(flags_dict)

    def get_waffle_flag_computed_status(self, flag):
        """
        Produce correct "computed_status" values for WaffleFlagCourseOverrideModel or
        WaffleFlagOrgOverrideModel instances.
        """
        computed_status = super().get_waffle_flag_computed_status(flag)
        # check course/org overrides only if computed_status is not already 'both'
        if computed_status != "both":
            has_force_on = False
            has_force_off = False
            for override_key in ("course_overrides", "org_overrides"):
                if override_key in flag:
                    has_force_on = has_force_on or any(
                        override["force"] == "on" for override in flag[override_key]
                    )
                    has_force_off = has_force_off or any(
                        override["force"] == "off" for override in flag[override_key]
                    )
            if has_force_on and has_force_off:
                computed_status = "both"
            elif has_force_on:
                computed_status = "on" if computed_status == "on" else "both"
            elif has_force_off:
                computed_status = "off" if computed_status == "off" else "both"
        return computed_status


class ToggleStateView(views.APIView):
    """
    An endpoint for displaying the state of toggles in edx-platform.
    """

    authentication_classes = (
        JwtAuthentication,
        SessionAuthentication,
    )
    permission_classes = (IsStaff,)

    def get(self, request):
        """
        Expose toggle state report dict as a view.
        """
        report = OverrideToggleStateReport().as_dict()
        return Response(report)


class FlagOverride(Enum):
    """
    Enumerates the supported CourseWaffleFlag overrides.
    """
    COURSE = "COURSE"
    ORG = "ORG"


def _add_waffle_flag_override_states(flags_dict):
    """
    Add waffle flag courserun & org override state from both the
    WaffleFlagCourseOverrideModel and WaffleFlagOrgOverrideModel models.
    """
    for override_type, override_key in (
        (FlagOverride.COURSE, "course_overrides"),
        (FlagOverride.ORG, "org_overrides")
    ):
        flag_overrides = _get_flag_overrides(override_type)
        for flag_name, overrides_dict in flag_overrides.items():
            enabled_overrides = [
                override
                for override in overrides_dict.values()
                if not override.get("disabled")
            ]
            if enabled_overrides:
                flag = get_or_create_toggle_response(flags_dict, flag_name)
                flag[override_key] = enabled_overrides


def _get_flag_overrides(course_or_org: FlagOverride):
    """
    Return flag objects from the requested override model instances.
    """
    # This dict is keyed by flag name, and contains dicts keyed by organization name, the contains
    # the final dict of metadata for a single course override that will be returned.
    flag_overrides = OrderedDict()
    # Note: We can't just get enabled records, because if a historical record is enabled but
    # the current record is disabled, we would not know this. We get all records, and mark
    # some overrides as disabled, and then later filter the disabled records.
    if course_or_org == FlagOverride.COURSE:
        override_key = "course_id"
        overrides_data = WaffleFlagCourseOverrideModel.objects.all().order_by(
            "waffle_flag", "course_id", "-change_date"
        )
    elif course_or_org == FlagOverride.ORG:
        override_key = "org"
        overrides_data = WaffleFlagOrgOverrideModel.objects.all().order_by(
            "waffle_flag", "org", "-change_date"
        )
    else:
        return {}

    for override in overrides_data:
        if course_or_org == FlagOverride.COURSE:
            override_match_val = str(override.course_id)
        elif course_or_org == FlagOverride.ORG:
            override_match_val = str(override.org)

        if override.enabled:
            override_fields = {
                "force": override.override_choice,
                "modified": str(override.change_date),
            }
        else:
            # The current record may be disabled, but later history might be enabled.
            # Disabled records are filtered elsewhere.
            override_fields = {"disabled": True}

        one_override = flag_overrides.setdefault(
            override.waffle_flag, OrderedDict()
        ).setdefault(
            override_match_val, OrderedDict()
        )
        # data is reverse ordered by date, so the first record is the current record
        if override_key not in one_override:
            one_override[override_key] = override_match_val
            one_override.update(override_fields)
        # data is reverse ordered by date, so the last record is the oldest record
        one_override["created"] = str(override.change_date)
    return flag_overrides
