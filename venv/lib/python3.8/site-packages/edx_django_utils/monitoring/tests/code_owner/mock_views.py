"""
Mock views with a different module to enable testing of mapping
code_owner to modules. Trying to mock __module__ on a view was
getting too complex.
"""
from django.views.generic import View


class MockViewTest(View):
    """
    Mock view for use in testing.
    """
