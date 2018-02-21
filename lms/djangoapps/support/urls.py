"""
URLs for the student support app.
"""
from django.conf.urls import url

from lms.djangoapps.support.views.contact_us import ContactUsView
from support.views.certificate import CertificatesSupportView
from support.views.course_entitlements import EntitlementSupportView, EntitlementSupportListView
from support.views.enrollments import EnrollmentSupportListView, EnrollmentSupportView
from support.views.index import index
from support.views.manage_user import ManageUserDetailView, ManageUserSupportView
from support.views.refund import RefundSupportView

COURSE_ENTITLEMENTS_VIEW = EntitlementSupportView.as_view()#{
#     'get': 'list',
#     'post': 'create',
#     'put': 'update'
# })
COURSE_ENTITLEMENTS_LIST_VIEW = EntitlementSupportListView.as_view({
    'get': 'list',
    'post': 'create',
    'put': 'update'
})

urlpatterns = [
    url(r'^$', index, name="index"),
    url(r'^certificates/?$', CertificatesSupportView.as_view(), name="certificates"),
    url(r'^refund/?$', RefundSupportView.as_view(), name="refund"),
    url(r'^course_entitlement/?$', COURSE_ENTITLEMENTS_VIEW, name="course_entitlement"),
    url(r'^entitlement_list/(?P<username_or_email>[\w.@+-]+)?$', COURSE_ENTITLEMENTS_LIST_VIEW, name="course_entitlement_list"),

    url(r'^enrollment/?$', EnrollmentSupportView.as_view(), name="enrollment"),
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
]
