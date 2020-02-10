"""
Utils for tests related to ecommerce
"""
from django.conf import settings


def get_ecommerce_host_url():
    return settings.ECOMMERCE_API_URL.strip('/api/v2/')


def make_ecommerce_url(url):
    return '{}{}'.format(get_ecommerce_host_url(), url)
