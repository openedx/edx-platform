"""Learner dashboard URL routing configuration"""


from django.conf.urls import url

from lms.djangoapps.learner_dashboard import programs, views

urlpatterns = [
    url(r'^programs/$', views.program_listing, name='program_listing_view'),
    url(r'^programs/(?P<program_uuid>[0-9a-f-]+)/$', views.program_details, name='program_details_view'),
    url(r'^programs_fragment/$', programs.ProgramsFragmentView.as_view(), name='program_listing_fragment_view'),
    url(r'^programs/(?P<program_uuid>[0-9a-f-]+)/details_fragment/$', programs.ProgramDetailsFragmentView.as_view(),
        name='program_details_fragment_view'),
]
