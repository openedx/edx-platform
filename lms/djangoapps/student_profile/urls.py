from django.conf.urls import patterns, url


USERNMAE_PATTERN = '(?P<username>[\w.@+-]+)'

urlpatterns = patterns(
    'student_profile.views',
    url(r'^profile/{username}$'.format(username=USERNMAE_PATTERN), 'learner_profile', name='learner_profile'),
)