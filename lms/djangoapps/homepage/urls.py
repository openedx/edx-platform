from django.conf.urls import url
from lms.djangoapps.homepage.views import home_page

urlpatterns = [
    url(r'^$', home_page, name='homepage'),
]
