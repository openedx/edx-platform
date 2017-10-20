from django.conf import settings


def pytest_configure():
    """
    Use Django's default settings for tests in common/lib.
    """
    settings.configure()
