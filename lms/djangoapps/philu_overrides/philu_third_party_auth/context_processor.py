"""
PhilU third party auth context processors
"""
import json

from openedx.core.djangoapps.user_authn.views.login_form import _third_party_auth_context

from .helpers import normalize_pipeline_kwargs


def get_third_party_auth_urls(request):
    """
    Since registration popups can be on any page, this context processor adds
    third_party_auth_context to the context
    """
    if request.user.is_authenticated:
        return dict()

    third_party_auth_context = _third_party_auth_context(request, request.path)
    third_party_form_fields = {}

    if third_party_auth_context['currentProvider']:
        third_party_form_fields = normalize_pipeline_kwargs(third_party_auth_context['pipeline_user_details'])
        utm_params = request.session.get('utm_params')

        if utm_params:
            try:
                third_party_form_fields['utm_params'] = json.loads(utm_params)
            except:  # pylint: disable=bare-except
                third_party_form_fields['utm_params'] = {}

    return {
        'third_party_auth_context': third_party_auth_context,
        'third_party_form_fields': third_party_form_fields
    }
