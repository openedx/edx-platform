"""
Views related to the Edly app feature.
"""

from django.shortcuts import render


def account_deactivated_view(request):
    return render(request=request, template_name="account_deactivated.html")
