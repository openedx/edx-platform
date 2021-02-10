"""
Views for the V1 Program Learner Dashboard API.
"""
from django.http import Http404
from edx_rest_framework_extensions.auth.jwt.authentication import JwtAuthentication
from rest_framework import authentication, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import (
    ProgramProgressMeter,
    get_program_marketing_url,
)


def _reformat_progress(progress_list):
    """
    This method formats the progress data into a format that is useful for connecting to programs.
    Args:
        progress_list (list): A list of dictionaries containing the progress data for each program.
    Returns:
        simplified_progress (dict): A dictionary with all of the progress status by program UUID.
    """
    simplified_progress = {}
    for progress in progress_list:
        uuid = progress.get('uuid', None)
        if uuid:
            simplified_progress[uuid] = {
                'completed': progress.get('completed', ''),
                'in_progress': progress.get('in_progress', ''),
                'not_started': progress.get('not_started', ''),
            }
    return simplified_progress


def _prepare_program_context(programs, progress):
    """
    This method takes the larger program data and reduces it to the set of required data. It
    also adds the progress data to each programs data object.

    Args:
        programs (list): A list of dictionaries containing program data.
        progress (list): A list of dictionaries containing the progress data for each program.
    Returns:
         context (dict): A dictionary containing the programs list with the progress included.
    """
    context = {}
    short_program_list = []
    progress_update = _reformat_progress(progress)

    for program in programs:
        uuid = program.get('uuid', '')
        program_progress = progress_update.get(uuid, {})
        short_program = {
            'uuid': uuid,
            'title': program.get('title', ''),
            'subtitle': program.get('subtitle', ''),
            'type': program.get('type', ''),
            'type_attrs': program.get('type_attrs', {}),
            'marketing_url': program.get('marketing_url', ''),
            'banner_image': program.get('banner_image', {}),
            'authoring_organizations': program.get('authoring_organizations', {}),
            'progress': program_progress,
        }
        short_program_list.append(short_program)
    context['programs'] = short_program_list
    return context


class ProgramListView(APIView):
    """
    This is an APIView for the Program list endpoint. This endpoint returns a simplified version of a
    user's current program enrollments. The program data provided is limited to just what the frontend
    of this API requires.

    The response will contain a list of data objects containing summary data about each program
    and the user's progress in that program.
    """
    authentication_classes = (
        JwtAuthentication,
        authentication.SessionAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Return a list programs a user is enrolled in.
        """
        user = request.user

        programs_config = ProgramsApiConfig.current()
        if not programs_config.enabled:
            raise Http404

        meter = ProgramProgressMeter(site=request.site, user=user)
        context = _prepare_program_context(meter.engaged_programs, meter.progress())
        context['marketing_url'] = get_program_marketing_url(programs_config)

        return Response(context)
