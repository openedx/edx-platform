
from xmodule.modulestore.django import modulestore
from xmodule.course_module import CourseDescriptor
from django.conf import settings


def get_subdomain(domain):
    return domain.split(".")[0]


def get_visible_courses(domain=None):
    """
    Return the set of CourseDescriptors that should be visible in this branded instance
    """
    courses = [c for c in modulestore().get_courses()
               if isinstance(c, CourseDescriptor)]
    courses = sorted(courses, key=lambda course: course.number)

    if domain and settings.MITX_FEATURES.get('SUBDOMAIN_COURSE_LISTINGS'):
        subdomain = get_subdomain(domain)
        if subdomain not in settings.COURSE_LISTINGS:
            subdomain = 'default'
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

    subdomain = get_subdomain(domain)
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
