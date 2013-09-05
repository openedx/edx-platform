from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView

from verify_student import views

urlpatterns = patterns(
    '',
    url(
        r'^show_requirements/(?P<course_id>[^/]+/[^/]+/[^/]+)$',
        views.show_requirements,
        name="verify_student_show_requirements"
    ),

    url(
        r'^verify/(?P<course_id>[^/]+/[^/]+/[^/]+)$',
        views.VerifyView.as_view(),
        name="verify_student_verify"
    ),

    url(
        r'^verified/(?P<course_id>[^/]+/[^/]+/[^/]+)$',
        views.VerifiedView.as_view(),
        name="verify_student_verified"
    ),

    url(
        r'^create_order',
        views.create_order,
        name="verify_student_create_order"
    ),

    url(
        r'^show_verification_page/(?P<course_id>[^/]+/[^/]+/[^/]+)$',
        views.show_verification_page,
        name="verify_student/show_verification_page"
    ),

)
