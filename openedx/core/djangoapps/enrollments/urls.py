"""
URLs for the Enrollment API

"""


from django.conf import settings
from django.urls import path, re_path

from .views import (
    CourseEnrollmentsApiListView,
    EnrollmentCourseDetailView,
    EnrollmentListView,
    EnrollmentUserRolesView,
    EnrollmentView,
    UnenrollmentView,
    #LiveClassesApiListView,
    LiveClassesListApiListView ,
    #LiveClassesDeleteApiView,
    EnrollLiveClassDetailsView,
    # EnrollLiveClassUserDetailsView,
    # EnrollLiveClassUserDetailsView,
)

urlpatterns = [
    re_path(r'^enrollment/{username},{course_key}$'.format(
        username=settings.USERNAME_PATTERN,
        course_key=settings.COURSE_ID_PATTERN),
        EnrollmentView.as_view(), name='courseenrollment'),
    re_path(fr'^enrollment/{settings.COURSE_ID_PATTERN}$',
            EnrollmentView.as_view(), name='courseenrollment'),
    path('enrollment', EnrollmentListView.as_view(), name='courseenrollments'),
    re_path(r'^enrollments/?$', CourseEnrollmentsApiListView.as_view(), name='courseenrollmentsapilist'),
    re_path(fr'^course/{settings.COURSE_ID_PATTERN}$',
            EnrollmentCourseDetailView.as_view(), name='courseenrollmentdetails'),
    path('unenroll/', UnenrollmentView.as_view(), name='unenrollment'),
    path('roles/', EnrollmentUserRolesView.as_view(), name='roles'),

    # re_path(r'^enrollment/{username}/live_class'.format(
    #         username=settings.USERNAME_PATTERN),
    #         LiveClassesApiListView.as_view(), name='course_live_class'),

        # path('enrollment/<username>/live_class', LiveClassesApiListView.as_view(), name='user_live_class' ),


        # path('enrollment/live_class/<id>', LiveClassesDeleteApiView.as_view(), name='live_class_delete' ),

#     re_path(r'^enrollment/{course_id}/live_class/{id}'.format(
#             course_id=settings.COURSE_ID_PATTERN,
#             id=settings.LIVE_CLASS_ID_PATTERN),
#             LiveClassesDeleteApiView.as_view(), name='course_live_class_delete'),

    re_path(r'^enrollments/live_class/?$', LiveClassesListApiListView.as_view(), name='live_class_list'),

    path('enrollment/live_class/enroll', EnrollLiveClassDetailsView.as_view(), name='user_live_class_details' ),

    # path('enrollment/live_class/enroll/detail/<live_class_id>', EnrollLiveClassUserDetailsView.as_view(), name='user_live_class_details' ),

    # path('enrollment/live_class/enroll/live_class/detail/<id>', EnrollLiveClassUserDetailsView.as_view(), name='user_live_class_details' ),
]