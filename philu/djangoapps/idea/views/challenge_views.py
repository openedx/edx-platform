# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Create your views here.
from django.views.generic import TemplateView


class ChallengeLandingView(TemplateView):
    template_name = 'philu/philuapps/idea/templates/challenges-landing-template.html'
