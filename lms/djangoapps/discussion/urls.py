"""
Forum urls for the django_comment_client.
"""


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'users/(?P<user_id>\w+)/followed$', views.followed_threads, name='followed_threads'),
    url(r'users/(?P<user_id>\w+)$', views.user_profile, name='user_profile'),
    url(r'^(?P<discussion_id>[\w\-.]+)/threads/(?P<thread_id>\w+)$', views.single_thread,
        name='single_thread'),
    url(r'^(?P<discussion_id>[\w\-.]+)/inline$', views.inline_discussion, name='inline_discussion'),
    url(
        r'discussion_board_fragment_view$',
        views.DiscussionBoardFragmentView.as_view(),
        name='discussion_board_fragment_view'
    ),
    url(r'', views.forum_form_discussion, name='forum_form_discussion'),
]
