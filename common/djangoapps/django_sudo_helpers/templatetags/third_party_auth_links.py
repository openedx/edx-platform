"""
Template tags and filters to display third party auth links on sudo page.
"""
from django import template
from django.template.response import TemplateResponse

from third_party_auth.pipeline import AUTH_ENTRY_SUDO
from third_party_auth import pipeline, is_enabled as is_third_party_auth_enabled


register = template.Library()   # pylint: disable=invalid-name


@register.simple_tag(name="third_party_auth_links", takes_context=True)
def third_party_auth_links(context):
    """
    Django template tag that outputs the third party auth links for sudo page.
    {% third_party_auth_links %}
    """
    request = context['request']
    auth_states = pipeline.get_provider_user_states(request.user)
    if is_third_party_auth_enabled():
        from student.helpers import auth_pipeline_urls, get_next_url_for_login_page

        redirect_to = get_next_url_for_login_page(request)
        third_party_auth_context = {
            'pipeline_url': auth_pipeline_urls(AUTH_ENTRY_SUDO, redirect_url=redirect_to),
            'has_enabled_account': any(state.has_account for state in auth_states),
            'providers': [{
                'provider_id': state.provider.provider_id,
                'has_account': state.has_account,
                'name': state.provider.name,
                'icon_class': state.provider.icon_class
            } for state in auth_states],
        }
        response = TemplateResponse(request, 'sudo/third_party_auth_links.html', third_party_auth_context).render()

        return response.content

    return ""


@register.filter
def get_pipeline_url(pipeline_url_dict, key):
    """
    Django template filter to get dict value.
    """
    return pipeline_url_dict.get(key)
