from django.conf.urls import url

urlpatterns = (
    url(r'^dev_mode$', 'contentstore.views.dev.dev_mode', name='dev_mode'),
)
