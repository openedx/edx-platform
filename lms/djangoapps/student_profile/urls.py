from django.conf.urls import patterns, url

urlpatterns = patterns(
    'student_profile.views',
    url(r'^$', 'index', name='profile_index'),
    url(r'^name_change$', 'name_change_handler', name='name_change'),
    url(r'^language_change$', 'language_change_handler', name='language_change'),
)
