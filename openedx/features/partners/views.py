from importlib import import_module

from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import Partner


def dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    try:
        views = import_module('openedx.features.partners.{slug}.views'.format(slug=partner.slug))
        return views.dashboard(request, partner.slug)
    except ImportError:
        raise Http404('Your partner is not properly registered')
