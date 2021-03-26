"""
Views that we will use to view toggle state in edx-platform.
"""
from collections import OrderedDict

from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from edx_rest_framework_extensions.permissions import IsStaff
from edx_toggles.toggles.state import ToggleStateReport, get_or_create_toggle_response
from rest_framework import views
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from .models import WaffleFlagCourseOverrideModel


class CourseOverrideToggleStateReport(ToggleStateReport):
    """
    Override some of the methods from ToggleStateReport to expose toggles from WaffleFlagCourseOverrideModel objects.
    """

    def add_waffle_flag_instances(self, flags_dict):
        """
        Append objects from WaffleFlagCourseOverrideModel.
        """
        super().add_waffle_flag_state(flags_dict)
        _add_waffle_flag_course_override_state(flags_dict)

    def get_waffle_flag_computed_status(self, flag):
        """
        Produce correct "computed_status" values for WaffleFlagCourseOverrideModel instances.
        """
        computed_status = super().get_waffle_flag_computed_status(flag)
        # check course overrides only if computed_status is not already 'both'
        if computed_status != "both" and "course_overrides" in flag:
            has_force_on = any(
                override["force"] == "on" for override in flag["course_overrides"]
            )
            has_force_off = any(
                override["force"] == "off" for override in flag["course_overrides"]
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
        report = CourseOverrideToggleStateReport().as_dict()
        return Response(report)


def _add_waffle_flag_course_override_state(flags_dict):
    """
    Add waffle flag course override state from the WaffleFlagCourseOverrideModel model.
    """

    flag_course_overrides = _get_flag_course_overrides()
    for flag_name, course_overrides_dict in flag_course_overrides.items():
        course_overrides = [
            course_override
            for course_override in course_overrides_dict.values()
            if not course_override.get("disabled")
        ]
        if course_overrides:
            flag = get_or_create_toggle_response(flags_dict, flag_name)
            flag["course_overrides"] = course_overrides


def _get_flag_course_overrides():
    """
    Return flag objects from WaffleFlagCourseOverrideModel instances.
    """
    # This dict is keyed by flag name, and contains dicts keyed by course_id, the contains
    # the final dict of metadata for a single course override that will be returned.
    flag_course_overrides = OrderedDict()
    # Note: We can't just get enabled records, because if a historical record is enabled but
    # the current record is disabled, we would not know this. We get all records, and mark
    # some overrides as disabled, and then later filter the disabled records.
    course_overrides_data = WaffleFlagCourseOverrideModel.objects.all().order_by(
        "waffle_flag", "course_id", "-change_date"
    )
    for course_override_data in course_overrides_data:
        if course_override_data.enabled:
            course_override_fields = {
                "force": course_override_data.override_choice,
                "modified": str(course_override_data.change_date),
            }
        else:
            # The current record may be disabled, but later history might be enabled.
            # We'll filter these disabled records below.
            course_override_fields = {"disabled": True}
        course_override_created_at = str(course_override_data.change_date)

        flag_name = course_override_data.waffle_flag
        course_id = str(course_override_data.course_id)
        course_override = flag_course_overrides.setdefault(
            flag_name, OrderedDict()
        ).setdefault(course_id, OrderedDict())
        # data is reverse ordered by date, so the first record is the current record
        if "course_id" not in course_override:
            course_override["course_id"] = course_id
            course_override.update(course_override_fields)
        # data is reverse ordered by date, so the last record is the oldest record
        course_override["created"] = course_override_created_at
    return flag_course_overrides
