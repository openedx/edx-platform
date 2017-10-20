from common.lib.nodebb_client.client import NodeBBClient
from custom_settings.models import CustomSettings
from edxmako.shortcuts import render_to_response
from django.contrib.auth.models import AnonymousUser
from courseware.courses import get_courses


def home_page(request, user=AnonymousUser()):
    featured_courses = get_featured_courses(user)
    status_code, featured_categories = NodeBBClient().categories.featured()

    context = {
        'courses': featured_courses,
        'categories': featured_categories if status_code == 200 else [],
    }

    return render_to_response("homepage/homepage.html", context)


def get_featured_courses(user):
    courses = get_courses(user)
    featured_custom_settings = CustomSettings.objects.filter(is_featured=True).values_list('id', flat=True)
    return [course for course in courses if str(course.id) in featured_custom_settings]
