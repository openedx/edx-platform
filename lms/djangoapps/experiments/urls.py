from django.conf.urls import include, url

from experiments import routers
from experiments.views import ExperimentDataViewSet

router = routers.DefaultRouter()
router.register(r'data', ExperimentDataViewSet, base_name='data')

urlpatterns = [
    url(r'^v0/', include(router.urls, namespace='v0')),
]
