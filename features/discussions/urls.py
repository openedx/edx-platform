"""
Forum urls for the django_comment_client.
"""
from django.conf.urls import url

from .views import DiscussionBoardFragmentView

urlpatterns = [
    url(
        r'users/(?P<user_id>\w+)/followed$',
        'features.discussions.views.followed_threads',
        name='edx.discussions.followed_threads'
    ),
    url(
        r'users/(?P<user_id>\w+)$',
        'features.discussions.views.user_profile',
        name='edx.discussions.user_profile'
    ),
    url(
        r'^(?P<discussion_id>[\w\-.]+)/threads/(?P<thread_id>\w+)$',
        'features.discussions.views.single_thread',
        name='edx.discussions.single_thread'
    ),
    url(
        r'^(?P<discussion_id>[\w\-.]+)/inline$',
        'features.discussions.views.inline_discussion',
        name='edx.discussions.inline_discussion'
    ),
    url(
        r'discussion_board_fragment_view$',
        DiscussionBoardFragmentView.as_view(),
        name='edx.discussions.discussion_board_fragment_view'
    ),
    url(
        r'',
        'features.discussions.views.forum_form_discussion',
        name='edx.discussions.forum_form_discussion'
    ),
]
