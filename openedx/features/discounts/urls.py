"""
Discount API URLs
"""


from django.conf import settings
from django.conf.urls import url

from .views import CourseUserDiscount, CourseUserDiscountWithUserParam

urlpatterns = [
    url(fr'^course/{settings.COURSE_KEY_PATTERN}', CourseUserDiscount.as_view(), name='course_user_discount'),
    url(fr'^user/(?P<user_id>[^/]*)/course/{settings.COURSE_KEY_PATTERN}',
        CourseUserDiscountWithUserParam.as_view(),
        name='course_user_discount_with_param'),
]
