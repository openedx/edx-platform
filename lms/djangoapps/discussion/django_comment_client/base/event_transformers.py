# pylint: skip-file
"""
Transformers for Discussion-related events.
"""


import six
from django.contrib.auth.models import User
from django.urls import NoReverseMatch, reverse
from eventtracking.processors.exceptions import EventEmissionExit
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator

from lms.djangoapps.discussion.django_comment_client.base.views import add_truncated_title_to_event_data
from lms.djangoapps.discussion.django_comment_client.permissions import get_team
from lms.djangoapps.discussion.django_comment_client.utils import get_cached_discussion_id_map_by_course_id
from common.djangoapps.track.transformers import EventTransformer, EventTransformerRegistry
from common.djangoapps.track.views.segmentio import BI_SCREEN_VIEWED_EVENT_NAME, FORUM_THREAD_VIEWED_EVENT_LABEL


def _get_string(dictionary, key, del_if_bad=True):
    """
    Get a string from a dictionary by key.

    If the key is not in the dictionary or does not refer to a string:
        - Return None
        - Optionally delete the key (del_if_bad)
    """
    if key in dictionary:
        value = dictionary[key]
        if isinstance(value, six.string_types):
            return value
        else:
            if del_if_bad:
                del dictionary[key]
            return None
    else:
        return None


@EventTransformerRegistry.register
class ForumThreadViewedEventTransformer(EventTransformer):
    """
    Transformer for forum-thread-viewed mobile navigation events.
    """

    match_key = BI_SCREEN_VIEWED_EVENT_NAME

    def process_event(self):
        """
        Process incoming mobile navigation events.

        For forum-thread-viewed events, change their names to
        edx.forum.thread.viewed and manipulate their data to conform with
        edx.forum.thread.viewed event design.

        Throw out other events.
        """

        # Get event context dict
        # Throw out event if context nonexistent or wrong type
        context = self.get('context')
        if not isinstance(context, dict):
            raise EventEmissionExit()

        # Throw out event if it's not a forum thread view
        if _get_string(context, 'label', del_if_bad=False) != FORUM_THREAD_VIEWED_EVENT_LABEL:
            raise EventEmissionExit()

        # Change name and event type
        self['name'] = 'edx.forum.thread.viewed'
        self['event_type'] = self['name']

        # If no event data, set it to an empty dict
        if 'event' not in self:
            self['event'] = {}
            self.event = {}

        # Throw out the context dict within the event data
        # (different from the context dict extracted above)
        if 'context' in self.event:
            del self.event['context']

        # Parse out course key
        course_id_string = _get_string(context, 'course_id') if context else None
        course_id = None
        if course_id_string:
            try:
                course_id = CourseLocator.from_string(course_id_string)
            except InvalidKeyError:
                pass

        # Change 'thread_id' field to 'id'
        thread_id = _get_string(self.event, 'thread_id')
        if thread_id:
            del self.event['thread_id']
            self.event['id'] = thread_id

        # Change 'topic_id' to 'commentable_id'
        commentable_id = _get_string(self.event, 'topic_id')
        if commentable_id:
            del self.event['topic_id']
            self.event['commentable_id'] = commentable_id

        # Change 'action' to 'title' and truncate
        title = _get_string(self.event, 'action')
        if title is not None:
            del self.event['action']
            add_truncated_title_to_event_data(self.event, title)

        # Change 'author' to 'target_username'
        author = _get_string(self.event, 'author')
        if author is not None:
            del self.event['author']
            self.event['target_username'] = author

        # Load user
        username = _get_string(self, 'username')
        user = None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                pass

        # If in a category, add category name and ID
        if course_id and commentable_id and user:
            id_map = get_cached_discussion_id_map_by_course_id(course_id, [commentable_id], user)
            if commentable_id in id_map:
                self.event['category_name'] = id_map[commentable_id]['title']
                self.event['category_id'] = commentable_id

        # Add thread URL
        if course_id and commentable_id and thread_id:
            url_kwargs = {
                'course_id': course_id_string,
                'discussion_id': commentable_id,
                'thread_id': thread_id
            }
            try:
                self.event['url'] = reverse('single_thread', kwargs=url_kwargs)
            except NoReverseMatch:
                pass

        # Add user's forum and course roles
        if course_id and user:
            self.event['user_forums_roles'] = [
                role.name for role in user.roles.filter(course_id=course_id)
            ]
            self.event['user_course_roles'] = [
                role.role for role in user.courseaccessrole_set.filter(course_id=course_id)
            ]

        # Add team ID
        if commentable_id:
            team = get_team(commentable_id)
            if team:
                self.event['team_id'] = team.team_id
