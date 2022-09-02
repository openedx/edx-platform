"""
URLs for genplus teach API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, ReflectionAnswerViewSet, ArticleViewLogViewSet, FiltersViewSet

app_name = 'genplus_teach_api_v1'

router = DefaultRouter()
router.register('articles', ArticleViewSet, basename='articles')


urlpatterns = (
    url(r'^portfolio/', ReflectionAnswerViewSet.as_view({"get": "portfolio"})),
    url(r'^filters/', FiltersViewSet.as_view({"get": "list"})),
    url(r'^articles/favorites/', ArticleViewSet.as_view({"get": "favorite_articles"})),
    url(r'^articles/(?P<pk>\d+)/add_favorite/', ArticleViewSet.as_view({"put": "add_favorite_article"})),
    url(r'^articles/(?P<pk>\d+)/rate/', ArticleViewSet.as_view({"put": "rate_article"})),
    url(r'^articles/(?P<pk>\d+)/log/', ArticleViewLogViewSet.as_view({"put": "log"})),
    url(r'^articles/(?P<article_id>\d+)/answer/', ReflectionAnswerViewSet.as_view({"put": "answer"})),
    path('', include(router.urls)),
)
