"""
Django storage backends for Open edX.
"""
from django.contrib.staticfiles.storage import StaticFilesStorage
from pipeline.storage import PipelineMixin, NonPackagingMixin
from require.storage import OptimizedFilesMixin
from openedx.core.djangoapps.theming.storage import ComprehensiveThemingStorage


class ProductionStorage(
        ComprehensiveThemingStorage,
        OptimizedFilesMixin,
        PipelineMixin,
        StaticFilesStorage
):
    """
    This class combines Django's StaticFilesStorage class with several mixins
    that provide additional functionality. We use this version on production.
    """
    pass


class DevelopmentStorage(
        ComprehensiveThemingStorage,
        NonPackagingMixin,
        PipelineMixin,
        StaticFilesStorage
):
    """
    This class combines Django's StaticFilesStorage class with several mixins
    that provide additional functionality. We use this version for development,
    so that we can skip packaging and optimization.
    """
    pass
