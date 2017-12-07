"""
Adaptive Learning
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie

from xmodule.modulestore.django import modulestore
from xmodule.util.adaptive_learning import AdaptiveLearningConfiguration

from adaptive_learning.utils import get_pending_reviews, get_revisions


@login_required
@ensure_csrf_cookie
def revisions(request):
    """
    Return a JSON list of all revisions for a user. Each revision includes a name, due date, and URL.
    """
    user = request.user

    pending_revisions = get_pending_revisions(user)
    json_revisions = json.dumps(pending_revisions)

    return HttpResponse(json_revisions)


def get_pending_revisions(user):
    """
    Return information about each problem that needs revision for a given user,
    including a display name, the due date of the revision, and a courseware URL.
    """
    # Get all courses:
    # Configuration for communicating with external service that provides adaptive learning features
    # is course-specific, so we need to collect pending revisions one course at a time.
    courses = modulestore().get_courses()

    # Initialize list of pending revisions
    pending_revisions = []

    # Collect pending revisions from each course
    for course in courses:

        # First, check if `course` has meaningful configuration for adaptive learning service;
        # if it doesn't, we can skip checking for pending reviews.
        if AdaptiveLearningConfiguration.is_meaningful(course.adaptive_learning_configuration):

            # Collect pending reviews for this `course` and current `user`
            pending_reviews = get_pending_reviews(course, user.id)

            # Create revision for each pending review, and add it to the list of pending revisions
            if pending_reviews:
                course_revisions = get_revisions(course, pending_reviews)
                pending_revisions.extend(course_revisions)

    return pending_revisions
