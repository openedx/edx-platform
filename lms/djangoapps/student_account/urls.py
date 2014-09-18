from django.conf.urls import patterns, url

urlpatterns = patterns(
    'student_account.views',
    url('', 'index', name='account_index')
)
