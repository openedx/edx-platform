"""
Experimentation URLs
"""


from django.conf.urls import include, url

from experiments import routers, views, views_custom

router = routers.DefaultRouter()
router.register(r'data', views.ExperimentDataViewSet, basename='data')
router.register(r'key-value', views.ExperimentKeyValueViewSet, basename='key_value')

urlpatterns = [
    url(r'^v0/custom/REV-934/', views_custom.Rev934.as_view(), name='rev_934'),
    url(r'^v0/', include((router.urls, "api"), namespace='v0')),
]
