from rest_framework import generics, status, views, viewsets
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db.models import Q
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from openedx.features.genplus_features.genplus.api.v1.permissions import IsTeacher
from openedx.core.djangoapps.cors_csrf.authentication import SessionAuthenticationCrossDomainCsrf
from openedx.features.genplus_features.genplus_teach.models import MediaType, Gtcs, Article, ArticleRating, \
    FavoriteArticle, ReflectionAnswer, Reflection, \
    ArticleViewLog, PortfolioEntry, Quote, AlertBarEntry, HelpGuide, HelpGuideRating
from openedx.features.genplus_features.genplus.api.v1.mixins import GenzMixin
from openedx.features.genplus_features.genplus.models import Teacher, Skill
from openedx.features.genplus_features.common.display_messages import SuccessMessages, ErrorMessages
from .serializers import (ArticleSerializer, FavoriteArticleSerializer, ArticleRatingSerializer,
                          ReflectionAnswerSerializer,ArticleViewLogSerializer, GtcsSerializer,
                          MediaTypeSerializer, PortfolioEntrySerializer, HelpGuideTypeSerializer,
                          AlertBarEntrySerializer, HelpGuideSerializer, GuideRatingSerializer)
from openedx.features.genplus_features.genplus.api.v1.serializers import SkillSerializer
from openedx.features.genplus_features.common.utils import get_generic_serializer
from .pagination import PortfolioPagination
from .filters import ArticleFilter
from drf_multiple_model.views import FlatMultipleModelAPIView


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

    def list(self, request, *args, **kwargs):
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        queryset = self.filter_queryset(self.get_queryset())
        favorite_queryset = self.queryset.filter(id__in=teacher.favorite_articles.values('article_id'))
        favorite_serializer = self.serializer_class(self.filter_queryset(favorite_queryset), many=True, context={
            'request': request,
            'teacher': teacher
        })
        response = {
            'favorites': favorite_serializer.data
        }
        page = self.paginate_queryset(queryset)
        if page is not None:
            articles_serializer = self.get_serializer(page, many=True)
            response['articles'] = self.get_paginated_response(articles_serializer.data).data
            return Response(response, status=status.HTTP_200_OK)

        response['articles'] = self.get_serializer(queryset, many=True).data

        return Response(response, status=status.HTTP_200_OK)

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
            # in case the favorite max tier is achieved
            if FavoriteArticle.objects.filter(teacher=teacher).count() >= FavoriteArticle.MAX_FAVORITE:
                return Response(ErrorMessages.MAX_FAVORITE.format(max=FavoriteArticle.MAX_FAVORITE),
                                status=status.HTTP_400_BAD_REQUEST)
            FavoriteArticle.objects.update_or_create(teacher=teacher, article=article)
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

        ArticleRating.objects.update_or_create(
            article=article,
            teacher=teacher,
            defaults=serializer.data
        )
        return Response(SuccessMessages.ARTICLE_RATED, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'])
    def featured(self, request):
        """
        featured article
        """
        article = get_object_or_404(Article, is_featured=True)
        serializer = self.serializer_class(article, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReflectionAnswerViewSet(viewsets.ViewSet, GenzMixin):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ReflectionAnswerSerializer

    @action(detail=True, methods=['put'])
    def answer(self, request, reflection_id=None):
        """
        answer the reflection
        """
        reflection = get_object_or_404(Reflection, pk=reflection_id)
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        ReflectionAnswer.objects.update_or_create(
            reflection=reflection, teacher=teacher,
            defaults={"answer": serializer.data.get('answer')}
        )
        return Response(SuccessMessages.REFLECTION_ADDED, status=status.HTTP_200_OK)


class ArticleViewLogViewSet(viewsets.ViewSet, GenzMixin):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = ArticleViewLogSerializer

    @action(detail=True, methods=['put'])
    def log(self, request, pk=None):
        """
        log views and engagement time on an article
        """
        article = get_object_or_404(Article, pk=pk)
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        count_time = serializer.data.get('count', 0)
        engagement_time = serializer.data.get('engagement', 0)
        try:
            log = ArticleViewLog.objects.get(teacher=teacher, article=article)
            log.count += count_time
            log.engagement += engagement_time
            log.save()
        except ArticleViewLog.DoesNotExist:
            ArticleViewLog.objects.create(
                teacher=teacher,
                article=article,
                **serializer.data
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class PortfolioViewSet(GenzMixin, viewsets.ViewSetMixin, FlatMultipleModelAPIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    sorting_fields = ['-created', ]
    sort_descending = True
    pagination_class = PortfolioPagination
    serializer_class = PortfolioEntrySerializer

    def _reflection_answer_filter(self, queryset, request, *args, **kwargs):
        query_params = self.request.query_params
        skill = query_params.get('skill')
        gtcs = query_params.get('gtcs')
        search = query_params.get('search', '')
        if skill:
            queryset = queryset.filter(reflection__article__skills__in=[skill, ])
        if gtcs:
            queryset = queryset.filter(reflection__article__gtcs__in=[gtcs, ])
        queryset = queryset.filter(Q(answer__icontains=search) | Q(reflection__article__title__icontains=search))
        return queryset

    def _portfolio_entry_filter(self, queryset, request, *args, **kwargs):
        query_params = self.request.query_params
        skill = query_params.get('skill')
        gtcs = query_params.get('gtcs')
        search = query_params.get('search', '')
        if skill:
            queryset = queryset.filter(skill=skill)
        if gtcs:
            queryset = queryset.filter(gtcs=gtcs)
        queryset = queryset.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return queryset

    def get_querylist(self):
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        reflection_answers = ReflectionAnswer.objects.filter(teacher=teacher)
        portfolio_entries = PortfolioEntry.objects.filter(teacher=teacher)
        return [
            {
                'queryset': reflection_answers,
                'serializer_class': get_generic_serializer({'name': ReflectionAnswer, 'fields': '__all__'},
                                                           depth_arg=2),
                'label': 'reflection_answer',
                'filter_fn': self._reflection_answer_filter
            },
            {
                'queryset': portfolio_entries,
                'serializer_class': get_generic_serializer({'name': PortfolioEntry, 'fields': '__all__'},
                                                           depth_arg=2),
                'label': 'portfolio_entry',
                'filter_fn': self._portfolio_entry_filter
            }
        ]

    def create(self, request, *args, **kwargs):
        request.data.update({'teacher': self.gen_user.teacher.id})
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(SuccessMessages.PORTFOLIO_ENTRY_ADDED, status=status.HTTP_200_OK)

    def get_serializer_context(self):
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        context = super(PortfolioViewSet, self).get_serializer_context()
        context.update({"teacher": teacher})
        return context


class PortfolioUpdateAPIView(GenzMixin, generics.UpdateAPIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = PortfolioEntrySerializer

    def get_queryset(self):
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        return PortfolioEntry.objects.filter(teacher=teacher)


class QuoteViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = get_generic_serializer({'name': Quote, 'fields': '__all__'}, )

    # @method_decorator(cache_page(60))
    @action(detail=True, methods=['get'])
    def list(self, request, *args, **kwargs):
        """ Quote of the week """
        quote = get_object_or_404(Quote, is_current=True)
        serializer = self.serializer_class(quote)
        return Response(serializer.data, status=status.HTTP_200_OK)


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


class HelpGuideViewSet(viewsets.ReadOnlyModelViewSet, GenzMixin):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = HelpGuideTypeSerializer
    pagination_class = None
    queryset = serializer_class.Meta.model.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['helpguide__title']
    
    def retrieve(self, request, pk=None):
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        guide = get_object_or_404(HelpGuide, pk=pk)
        serializer = HelpGuideSerializer(instance=guide, context={ 'teacher': teacher })
        return Response(serializer.data)
    
    @action(detail=True, methods=['put'])
    def rate_guide(self, request, pk=None):  # pylint: disable=unused-argument
        """
        rate the guide article
        """
        help_guide = HelpGuide.objects.get(pk=pk)
        teacher = Teacher.objects.get(gen_user=self.gen_user)
        serializer = GuideRatingSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        HelpGuideRating.objects.update_or_create(
            help_guide=help_guide,
            teacher=teacher,
            defaults=serializer.data
        )
        return Response(SuccessMessages.ARTICLE_RATED, status=status.HTTP_200_OK)

class AlertBarEntryView(generics.ListAPIView):
    authentication_classes = [SessionAuthenticationCrossDomainCsrf]
    permission_classes = [IsAuthenticated, IsTeacher]
    serializer_class = AlertBarEntrySerializer
    pagination_class = None

    def list(self, request, *args, **kwargs):
        alert_bar = get_object_or_404(AlertBarEntry, is_current=True)
        serializer = self.serializer_class(alert_bar)
        return Response(serializer.data, status=status.HTTP_200_OK)
