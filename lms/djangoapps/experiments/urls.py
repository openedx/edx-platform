from django.conf.urls import include, url

from experiments import routers, views

router = routers.DefaultRouter()
router.register(r'data', views.ExperimentDataViewSet, base_name='data')
router.register(r'key-value', views.ExperimentKeyValueViewSet, base_name='key_value')

app_name = 'experiments'
urlpatterns = [
    url(r'^v0/', include(router.urls, namespace='v0')),
]
