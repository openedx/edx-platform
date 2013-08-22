from django.conf.urls import include, patterns, url
from django.views.generic import TemplateView

from verify_student import views

urlpatterns = patterns(
    '',
    url(
        r'^show_requirements',
        views.show_requirements,
        name="verify_student/show_requirements"
    ),
    url(
        r'^face_upload',
        views.face_upload,
        name="verify_student/face_upload"
    ),
    url(
        r'^photo_id_upload',
        views.photo_id_upload,
        name="verify_student/photo_id_upload"
    ),
    url(
        r'^final_verification',
        views.final_verification,
        name="verify_student/final_verification"
    ),

    # The above are what we did for the design mockups, but what we're really
    # looking at now is:
    url(
        r'^show_verification_page',
        views.show_verification_page,
        name="verify_student/show_verification_page"
    ),

    url(
        r'^verify',
        views.VerifyView.as_view(),
        name="verify_student_verify"
    ),

    url(
        r'^create_order',
        views.create_order,
        name="verify_student_create_order"
    )

)
