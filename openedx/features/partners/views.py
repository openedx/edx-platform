from django.shortcuts import get_object_or_404
from g2a.views import g2a_dashboard
from .models import Partner


def dashboard(request, slug):
    partner = get_object_or_404(Partner, slug=slug)
    # TODO: we need to make it generic for all partners
    if partner.slug == 'give2asia':
        return g2a_dashboard(request)

