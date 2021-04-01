"""
All views for webinars app
"""
from django.shortcuts import redirect, render


def webinar_description_page_view(request):
    return render(request, 'adg/lms/webinar/description_page.html', context={})
