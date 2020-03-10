from common.lib.discovery_client.client import DiscoveryClient
from edxmako.shortcuts import render_to_response


def list_specializations(request):
    context = DiscoveryClient().active_programs()
    return render_to_response('features/specializations/list.html', context)


def specialization_about(request, specialization_uuid):
    return render_to_response('features/specializations/about.html', {})
