"""
URLs for the student support app.
"""


from django.conf.urls import url

from .views.contact_us import ContactUsView
from .views.certificate import CertificatesSupportView
from .views.course_entitlements import EntitlementSupportView
from .views.enrollments import EnrollmentSupportListView, EnrollmentSupportView
from .views.feature_based_enrollments import FeatureBasedEnrollmentsSupportView
from .views.index import index
from .views.manage_user import ManageUserDetailView, ManageUserSupportView
from .views.program_enrollments import LinkProgramEnrollmentSupportView, ProgramEnrollmentsInspectorView
from .views.sso_records import SsoView

COURSE_ENTITLEMENTS_VIEW = EntitlementSupportView.as_view()

app_name = 'support'
urlpatterns = [
    url(r'^$', index, name="index"),
    url(r'^certificates/?$', CertificatesSupportView.as_view(), name="certificates"),
    url(r'^enrollment/?$', EnrollmentSupportView.as_view(), name="enrollment"),
    url(r'^course_entitlement/?$', COURSE_ENTITLEMENTS_VIEW, name="course_entitlement"),
    url(r'^contact_us/?$', ContactUsView.as_view(), name="contact_us"),
    url(
        r'^enrollment/(?P<username_or_email>[\w.@+-]+)?$',
        EnrollmentSupportListView.as_view(),
        name="enrollment_list"
    ),
    url(r'^manage_user/?$', ManageUserSupportView.as_view(), name="manage_user"),
    url(
        r'^manage_user/(?P<username_or_email>[\w.@+-]+)?$',
        ManageUserDetailView.as_view(),
        name="manage_user_detail"
    ),
    url(
        r'^feature_based_enrollments/?$',
        FeatureBasedEnrollmentsSupportView.as_view(),
        name="feature_based_enrollments"
    ),
    url(r'link_program_enrollments/?$', LinkProgramEnrollmentSupportView.as_view(), name='link_program_enrollments'),
    url(
        r'program_enrollments_inspector/?$',
        ProgramEnrollmentsInspectorView.as_view(),
        name='program_enrollments_inspector'
    ),
    url(r'sso_records/(?P<username_or_email>[\w.@+-]+)?$', SsoView.as_view(), name='sso_records'),
]
