from django.conf.urls.defaults import url, patterns
import django_comment_client.base.views

urlpatterns = patterns('django_comment_client.base.views',

    url(r'upload$', 'upload', name='upload'),
    url(r'threads/(?P<thread_id>[\w\-]+)/update$', 'update_thread', name='update_thread'),
    url(r'threads/(?P<thread_id>[\w\-]+)/reply$', 'create_comment', name='create_comment'),
    url(r'threads/(?P<thread_id>[\w\-]+)/delete', 'delete_thread', name='delete_thread'),
    url(r'threads/(?P<thread_id>[\w\-]+)/upvote$', 'vote_for_thread', {'value': 'up'}, name='upvote_thread'),
    url(r'threads/(?P<thread_id>[\w\-]+)/downvote$', 'vote_for_thread', {'value': 'down'}, name='downvote_thread'),
    url(r'threads/(?P<thread_id>[\w\-]+)/watch$', 'watch_thread', name='watch_thread'),
    url(r'threads/(?P<thread_id>[\w\-]+)/unwatch$', 'unwatch_thread', name='unwatch_thread'),

    url(r'comments/(?P<comment_id>[\w\-]+)/update$', 'update_comment', name='update_comment'),
    url(r'comments/(?P<comment_id>[\w\-]+)/endorse$', 'endorse_comment', name='endorse_comment'),
    url(r'comments/(?P<comment_id>[\w\-]+)/reply$', 'create_sub_comment', name='create_sub_comment'),
    url(r'comments/(?P<comment_id>[\w\-]+)/delete$', 'delete_comment', name='delete_comment'),
    url(r'comments/(?P<comment_id>[\w\-]+)/upvote$', 'vote_for_comment', {'value': 'up'}, name='upvote_comment'),
    url(r'comments/(?P<comment_id>[\w\-]+)/downvote$', 'vote_for_comment', {'value': 'down'}, name='downvote_comment'),
    
    url(r'(?P<commentable_id>[\w\-]+)/threads/create$', 'create_thread', name='create_thread'),
    url(r'(?P<commentable_id>[\w\-]+)/watch$', 'watch_commentable', name='watch_commentable'),
    url(r'(?P<commentable_id>[\w\-]+)/unwatch$', 'unwatch_commentable', name='unwatch_commentable'),

    url(r'search$', 'search', name='search'),
)
