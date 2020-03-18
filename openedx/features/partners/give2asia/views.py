from edxmako.shortcuts import render_to_response

from openedx.features.partners.helpers import get_partner_recommended_courses


def dashboard(request, partner_slug):
    courses = get_partner_recommended_courses(partner_slug, request.user)
    return render_to_response('features/partners/g2a/dashboard.html', {'recommended_courses': courses,
                                                                       'slug': partner_slug})


def performance_dashboard(request, partner):
    return render_to_response('features/partners/g2a/performance_dashboard.html',
                              {'slug': partner.slug, 'performance_url': partner.performance_url})
