""" Program Enrollments API v1 URLs. """
from django.conf.urls import url

from lms.djangoapps.program_enrollments.api.v1.views import ProgramEnrollmentsView


app_name = 'lms.djangoapps.program_enrollments'

urlpatterns = [
    url(
        r'^programs/{program_key}/enrollments/$'.format(program_key=r'(?P<program_key>[0-9a-fA-F-]+)'),
        ProgramEnrollmentsView.as_view(),
        name='program_enrollments'
    ),
]
