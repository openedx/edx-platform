"""Utility functions for canvas integration"""
import logging
import requests
import time
from urllib.parse import urljoin

from django.conf import settings
from django.utils.translation import ugettext as _
from opaque_keys.edx.locator import CourseLocator

from courseware.courses import get_course_by_id
from remote_gradebook.views import enroll_emails_in_course, unenroll_non_staff_users_in_course


log = logging.getLogger(__name__)


def get_canvas_session():
    """
    Create a request session with the access token
    """
    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer {token}".format(token=settings.CANVAS_ACCESS_TOKEN)
    })
    return session


def list_canvas_enrollments(course_id):
    """
    Fetch canvas enrollments. This may take a while, so don't run in the request thread.

    Args:
        course_id (int): The canvas id for the course

    Returns:
        list of str: A list of email addresses for enrolled users
    """
    emails = []
    session = get_canvas_session()
    url = urljoin(settings.CANVAS_BASE_URL, "/api/v1/courses/{course_id}/enrollments".format(course_id=course_id))
    while url:
        resp = session.get(url)
        resp.raise_for_status()
        links = requests.utils.parse_header_links(resp.headers["link"])
        url = None
        for link in links:
            if link["rel"] == "next":
                url = link["url"]
                # TODO: what's an appropriate delay? Does edX have a standard for this?
                time.sleep(0.2)

        emails.extend([enrollment["user"]["login_id"] for enrollment in resp.json()])
    return emails


def sync_canvas_enrollments(course_key, canvas_course_id):
    """
    Fetch enrollments from canvas and update

    Args:
        course_key (str): The edX course key
        canvas_course_id (int): The canvas course id
    """
    emails = list_canvas_enrollments(canvas_course_id)

    course_key = CourseLocator.from_string(course_key)
    course = get_course_by_id(course_key)

    # Unenroll everyone first, in case someone has unenrolled
    unenrolled = unenroll_non_staff_users_in_course(course)
    log.info("Unenrolled non-staff users in course %s: %s", course_key, unenrolled)
    # Then re-enroll everyone
    enrolled = enroll_emails_in_course(emails=emails, course_key=course_key)
    log.info("Enrolled users in course %s: %s", course_key, enrolled)
