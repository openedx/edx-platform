from edxmako.shortcuts import render_to_response

from openedx.features.partners.helpers import get_partner_recommended_courses


def g2a_dashboard(request):
    # TODO: The argument must be dynamic after integration of LP-1632
    courses = get_partner_recommended_courses('give2asia')
    return render_to_response('partners/g2a/dashboard.html', {'recommended_courses': courses})
