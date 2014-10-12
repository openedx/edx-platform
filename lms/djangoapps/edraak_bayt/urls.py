from django.conf import settings
from django.conf.urls import patterns, url
from django.core.urlresolvers import LocaleRegexURLResolver


urlpatterns = patterns('',
        url(r'^get_student_email_for_bayt$', 'edraak_bayt.views.get_student_email', name="edraak_bayt_get_student_email"),
        url(r'^bayt-activation$', 'edraak_bayt.views.activation', name="bayt_activation"),
)
