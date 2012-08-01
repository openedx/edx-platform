from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.utils.http import urlquote  as django_urlquote

from simplewiki.wiki_settings import *

register = template.Library()


@register.filter()
def prepend_media_url(value):
    """Prepend user defined media root to url"""
    return settings.MEDIA_URL + value


@register.filter()
def urlquote(value):
    """Prepend user defined media root to url"""
    return django_urlquote(value)
