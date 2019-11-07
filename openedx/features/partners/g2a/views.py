from edxmako.shortcuts import render_to_response

from openedx.features.partners.helpers import get_partner_recommended_courses


def g2a_dashboard(request, partner_slug):
    courses = get_partner_recommended_courses(partner_slug)
    return render_to_response('partners/g2a/dashboard.html', {'recommended_courses': courses})
