from django.conf.urls import url

from .views import CourseOutlineView


urlpatterns = [
    url(
        r'^v1/course_outline/(?P<course_key_str>.+)$',
        CourseOutlineView.as_view(),
        name='course_outline',
    )
]
