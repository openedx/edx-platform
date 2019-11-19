from django.conf.urls import url

from .views import trophycase

urlpatterns = [
    url(r'^trophycase/$', trophycase, name="trophycase"),
]
