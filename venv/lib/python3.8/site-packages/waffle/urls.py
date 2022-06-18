from django.urls import path

from waffle.views import wafflejs

urlpatterns = [
    path('wafflejs', wafflejs, name='wafflejs'),
]
