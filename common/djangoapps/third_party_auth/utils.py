"""
Utility functions for third_party_auth module for both cms and lms
"""

from django.conf import settings

from microsite_configuration import microsite

from third_party_auth import pipeline, provider

def prepopulate_register_form(request, context):
    """
    Prepopulate the register form with data from the selected provider.
    """
    context.update({
        'email': '',
        'name': '',
        'username': '',
        'platform_name': microsite.get_value('platform_name', settings.PLATFORM_NAME),
        'pipeline_running': None,
    })

    if settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH') and pipeline.running(request):
        pipeline_running = pipeline.get(request)
        current_provider = provider.Registry.get_by_backend_name(pipeline_running.get('backend'))
        overrides = current_provider.get_register_form_data(pipeline_running.get('kwargs'))
        overrides['pipeline_running'] = pipeline_running
        overrides['selected_provider'] = current_provider.NAME
        context.update(overrides)
