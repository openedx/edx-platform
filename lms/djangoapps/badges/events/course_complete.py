"""
Helper functions for the course complete event that was originally included with the Badging MVP.
"""
import hashlib

from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from badges.utils import site_prefix


# NOTE: As these functions are carry-overs from the initial badging implementation, they are used in
# migrations. Please check the badge migrations when changing any of these functions.

def course_slug(course_key, mode):
    """
    Legacy: Not to be used as a model for constructing badge slugs. Included for compatibility with the original badge
    type, awarded on course completion.

    Slug ought to be deterministic and limited in size so it's not too big for Badgr.

    Badgr's max slug length is 255.
    """
    # Seven digits should be enough to realistically avoid collisions. That's what git services use.
    digest = hashlib.sha256(u"{}{}".format(unicode(course_key), unicode(mode))).hexdigest()[:7]
    base_slug = slugify(unicode(course_key) + u'_{}_'.format(mode))[:248]
    return base_slug + digest


def badge_description(course, mode):
    """
    Returns a description for the earned badge.
    """
    if course.end:
        return _(u'Completed the course "{course_name}" ({course_mode}, {start_date} - {end_date})').format(
            start_date=course.start.date(),
            end_date=course.end.date(),
            course_name=course.display_name,
            course_mode=mode,
        )
    else:
        return _(u'Completed the course "{course_name}" ({course_mode})').format(
            course_name=course.display_name,
            course_mode=mode,
        )


def evidence_url(user_id, course_key):
    """
    Generates a URL to the user's Certificate HTML view, along with a GET variable that will signal the evidence visit
    event.
    """
    return site_prefix() + reverse(
        'certificates:html_view', kwargs={'user_id': user_id, 'course_id': unicode(course_key)}) + '?evidence_visit=1'


def criteria(course_key):
    """
    Constructs the 'criteria' URL from the course about page.
    """
    about_path = reverse('about_course', kwargs={'course_id': unicode(course_key)})
    return u'{}{}'.format(site_prefix(), about_path)
