"""
URLs for genplus teach API v1.
"""
from django.conf.urls import url
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ArticleViewSet, ReflectionAnswerViewSet, ArticleViewLogViewSet, FiltersViewSet, \
    PortfolioViewSet, PortfolioUpdateAPIView, QuoteViewSet, HelpGuideViewSet, AlertBarEntryView

app_name = 'genplus_teach_api_v1'

router = DefaultRouter()
router.register('articles', ArticleViewSet, basename='articles')
router.register('portfolio', PortfolioViewSet, basename='portfolio')
router.register('help-guides', HelpGuideViewSet, basename='help-guides')


urlpatterns = (
    url(r'^filters/', FiltersViewSet.as_view({"get": "list"})),
    url(r'^quote/', QuoteViewSet.as_view({"get": "list"})),
    url(r'^alert-bar/', AlertBarEntryView.as_view()),
    url(r'^portfolio/(?P<pk>\d+)/', PortfolioUpdateAPIView.as_view()),
    url(r'^articles/(?P<pk>\d+)/add_favorite/', ArticleViewSet.as_view({"put": "add_favorite_article"})),
    url(r'^articles/(?P<pk>\d+)/rate/', ArticleViewSet.as_view({"put": "rate_article"})),
    url(r'^articles/featured/', ArticleViewSet.as_view({"get": "featured"})),
    url(r'^articles/(?P<pk>\d+)/log/', ArticleViewLogViewSet.as_view({"put": "log"})),
    url(r'^articles/(?P<reflection_id>\d+)/answer/', ReflectionAnswerViewSet.as_view({"put": "answer"})),
    url(r'^help-guides/(?P<pk>\d+)/rate/', HelpGuideViewSet.as_view({"put": "rate_guide"})),
    path('', include(router.urls)),
)
