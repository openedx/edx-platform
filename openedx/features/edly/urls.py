"""
URLs Edly app views.
"""

from django.conf.urls import url

from openedx.features.edly.views import account_deactivated_view

urlpatterns = [
    url('account_deactivated/', account_deactivated_view, name='account_deactivated_view'),
]
