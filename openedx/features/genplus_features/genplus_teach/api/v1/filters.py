import django_filters
from openedx.features.genplus_features.genplus_teach.models import MediaType, Gtcs, Article


class ArticleFilter(django_filters.FilterSet):
    skill = django_filters.NumberFilter(
        field_name='skills__id',
    )
    media_type = django_filters.NumberFilter(
        field_name='media_types__id',
    )
    gtcs = django_filters.NumberFilter(
        field_name='gtcs__id',
    )

    class Meta:
        model = Article
        fields = ('title', 'skill', 'media_types', 'gtcs')
