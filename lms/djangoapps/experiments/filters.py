import django_filters

from experiments.models import ExperimentData


class ExperimentDataFilter(django_filters.FilterSet):
    class Meta(object):
        model = ExperimentData
        fields = ['experiment_id', 'key', ]
