"""
Experimentation filters
"""


import django_filters

from lms.djangoapps.experiments.models import ExperimentData, ExperimentKeyValue


class ExperimentDataFilter(django_filters.FilterSet):
    class Meta(object):
        model = ExperimentData
        fields = ['experiment_id', 'key', ]


class ExperimentKeyValueFilter(django_filters.FilterSet):
    class Meta(object):
        model = ExperimentKeyValue
        fields = ['experiment_id', 'key', ]
