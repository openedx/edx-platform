"""
Overrides the branding api
"""
from django.urls import reverse


def get_home_url():
    """
    Return Home page url
    """
    return reverse('root')
