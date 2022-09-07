from rest_framework import generics, status, views, viewsets
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import F
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus_teach.models import MediaType, Gtcs, Article, ArticleRating, FavoriteArticle, ReflectionAnswer, Reflection, ArticleViewLog
from openedx.features.genplus_features.genplus.api.v1.mixins import GenzMixin
from openedx.features.genplus_features.genplus.models import Teacher, Skill
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages
from .serializers import ArticleSerializer, FavoriteArticleSerializer, ArticleRatingSerializer, ReflectionAnswerSerializer,\
    PortfolioSerializer, ArticleViewLogSerializer, GtcsSerializer, MediaTypeSerializer
from openedx.features.genplus_features.genplus.api.v1.serializers import SkillSerializer
from .filters import ArticleFilter


class ArticleViewSet(viewsets.ModelViewSet, GenzMixin):
    """
    Viewset for Articles APIs
    """
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ArticleSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['title', 'content']
    filter_fields = ('skill', 'media_type', 'gtcs')
    filterset_class = ArticleFilter
    queryset = Article.objects.exclude(is_draft=True)

    def get_serializer_context(self):
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        context = super(ArticleViewSet, self).get_serializer_context()
        context.update({"teacher": teacher})
        return context

    def get_queryset(self):
        print(self.action)
        queryset = self.queryset
        if self.action == 'list':
            teacher = Teacher.objects.get(gen_user=self.gen_user)
            queryset = queryset.exclude(id__in=teacher.favorite_articles.values('article_id'))
        return queryset.order_by('-created')

    @action(detail=True, methods=['get'])
    def favorite_articles(self, request, pk=None):  # pylint: disable=unused-argument
        """
        get favorite articles
        """
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        queryset = self.queryset.filter(id__in=teacher.favorite_articles.values('article_id'))
        serializer = self.serializer_class(queryset, many=True, context={'request': request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)

    @action(detail=True, methods=['put'])
    def add_favorite_article(self, request, pk=None):  # pylint: disable=unused-argument
        """
        add articles to favorites
        """
        serializer = FavoriteArticleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.data
        article = self.get_object()
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        if data['action'] == 'add':
            FavoriteArticle.objects.create(teacher=teacher, article=article)
            return Response(SuccessMessages.ARTICLE_ADDED_TO_FAVORITES.format(title=article.title),
                            status=status.HTTP_200_OK)
        else:
            FavoriteArticle.objects.filter(teacher=teacher, article=article).delete()
            return Response(SuccessMessages.ARTICLE_REMOVED_FROM_FAVORITES.format(title=article.title),
                            status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'])
    def rate_article(self, request, pk=None):  # pylint: disable=unused-argument
        """
        rate the article
        """
        article = self.get_object()
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        serializer = ArticleRatingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if ArticleRating.objects.filter(article=article, teacher=teacher).exists():
            return Response(ErrorMessages.ARTICLE_ALREADY_RATED, status=status.HTTP_400_BAD_REQUEST)

        ArticleRating.objects.create(
            article=article,
            teacher=teacher,
            **serializer.data
        )
        return Response(SuccessMessages.ARTICLE_RATED, status=status.HTTP_204_NO_CONTENT)


class ReflectionAnswerViewSet(viewsets.ViewSet, GenzMixin):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ReflectionAnswerSerializer
    portfolio_serializer_class = PortfolioSerializer

    @action(detail=True, methods=['put'])
    def answer(self, request, article_id=None):
        """
        answer the reflection
        """
        article = get_object_or_404(Article, pk=article_id)
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ReflectionAnswer.objects.update_or_create(
            article=article, teacher=teacher,
            defaults={"answer": serializer.data.get('answer')}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def portfolio(self, request):
        """
        teacher portfolio
        """
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        qs = ReflectionAnswer.objects.filter(teacher=teacher)
        serializer = self.portfolio_serializer_class(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ArticleViewLogViewSet(viewsets.ViewSet, GenzMixin):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ArticleViewLogSerializer

    @action(detail=True, methods=['put'])
    def log(self, request, article_id=None):
        """
        log views and engagement time on an article
        """
        article = get_object_or_404(Article, pk=article_id)
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        count_time = serializer.data.get('count', 0)
        engagement_time = serializer.data.get('engagement', 0)
        try:
            log = ArticleViewLog.objects.get(teacher=teacher, article=article)
            log.udpate(
                        count=F('count') + count_time,
                        engagement=F('engagement') + engagement_time
                       )
        except ArticleViewLog.DoesNotExist:
            ArticleViewLog.objects.create(
                teacher=teacher,
                article=article,
                **serializer.data
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class FiltersViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]

    @method_decorator(cache_page(60))
    @action(detail=True, methods=['get'])
    def list(self, request, *args, **kwargs):
        gtcs_serializer = GtcsSerializer(Gtcs.objects.all(), many=True)
        skills_serializer = SkillSerializer(Skill.objects.all(), many=True)
        media_type_serializer = MediaTypeSerializer(MediaType.objects.all(), many=True)
        data = {
            'gtcs': gtcs_serializer.data,
            'skills': skills_serializer.data,
            'media_types': media_type_serializer.data
        }
        return Response(data)
