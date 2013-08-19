from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from django.conf import settings


def pick_subdomain(domain, options, default='default'):
    for option in options:
        if domain.startswith(option):
            return option
    return default


def get_visible_courses(domain=None):
    """
    Return the set of CourseDescriptors that should be visible in this branded instance
    """
    _courses = modulestore().get_courses()

    courses = [c for c in _courses
               if isinstance(c, CourseDescriptor)]
    courses = sorted(courses, key=lambda course: course.number)

    if domain and settings.MITX_FEATURES.get('SUBDOMAIN_COURSE_LISTINGS'):
        subdomain = pick_subdomain(domain, settings.COURSE_LISTINGS.keys())
        visible_ids = frozenset(settings.COURSE_LISTINGS[subdomain])
        return [course for course in courses if course.id in visible_ids]
    else:
        return courses


def get_university(domain=None):
    """
    Return the university name specified for the domain, or None
    if no university was specified
    """
    if not settings.MITX_FEATURES['SUBDOMAIN_BRANDING'] or domain is None:
        return None

    subdomain = pick_subdomain(domain, settings.SUBDOMAIN_BRANDING.keys())
    return settings.SUBDOMAIN_BRANDING.get(subdomain)


def get_logo_url(domain=None):
    """
    Return the url for the branded logo image to be used
    """
    university = get_university(domain)

    if university is None:
        return '/static/images/header-logo.png'

    return '/static/images/{uni}-on-edx-logo.png'.format(
        uni=university
    )
