from django.conf.urls import patterns, url

urlpatterns = patterns(
    'student_profile.views',
    url(r'^$', 'index', name='profile_index'),
    url(r'^preferences$', 'preference_handler', name='preference_handler'),
    url(r'^preferences/languages$', 'language_info', name='language_info'),
)
