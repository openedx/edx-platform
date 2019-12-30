"""
Experimentation URLs
"""


from django.conf.urls import include, url

from experiments import routers, views, views_custom

router = routers.DefaultRouter()
router.register(r'data', views.ExperimentDataViewSet, base_name='data')
router.register(r'key-value', views.ExperimentKeyValueViewSet, base_name='key_value')

app_name = 'lms.djangoapps.experiments'

urlpatterns = [
    url(r'^v0/custom/REV-934/', views_custom.Rev934.as_view(), name='rev_934'),
    url(r'^v0/', include(router.urls, namespace='v0')),
]
