# lint-amnesty, pylint: disable=missing-module-docstring

from django.http import HttpResponse

from common.djangoapps.student.models import UserProfile


def mock_render_to_string(template_name, context):
    """
    Return a string that encodes template_name and context
    """
    return str((template_name, sorted(context.items())))


def mock_render_to_response(template_name, context):
    """
    Return an HttpResponse with content that encodes template_name and context
    """
    # This simulates any db access in the templates.
    UserProfile.objects.exists()
    return HttpResponse(mock_render_to_string(template_name, context))
