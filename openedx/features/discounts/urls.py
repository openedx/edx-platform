"""
Discount API URLs
"""


from django.conf import settings

from .views import CourseUserDiscount, CourseUserDiscountWithUserParam
from django.urls import re_path

urlpatterns = [
    re_path(fr'^course/{settings.COURSE_KEY_PATTERN}', CourseUserDiscount.as_view(), name='course_user_discount'),
    re_path(fr'^user/(?P<user_id>[^/]*)/course/{settings.COURSE_KEY_PATTERN}',
            CourseUserDiscountWithUserParam.as_view(),
            name='course_user_discount_with_param'),
]
