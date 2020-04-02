from django.conf.urls import include, url

urlpatterns = [
    url(r'', include('philu.djangoapps.marketplace.urls')),
    url(r'', include('philu.djangoapps.idea.urls')),
]
