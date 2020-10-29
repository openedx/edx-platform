"""
Discount API URLs
"""


from django.conf import settings
from django.conf.urls import url

from .views import CourseUserDiscount, CourseUserDiscountWithUserParam

urlpatterns = [
    url(r'^course/{}'.format(settings.COURSE_KEY_PATTERN), CourseUserDiscount.as_view(), name='course_user_discount'),
    url(r'^user/(?P<user_id>[^/]*)/course/{}'.format(settings.COURSE_KEY_PATTERN),
        CourseUserDiscountWithUserParam.as_view(),
        name='course_user_discount_with_param'),
]
