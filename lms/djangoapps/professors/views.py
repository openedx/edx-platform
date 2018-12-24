# -*- coding: utf-8 -*-
"""
User-facing views for the Membership app.
"""
from __future__ import unicode_literals

from edxmako.shortcuts import render_to_response


def professors_index(request):
    context = {

    }
    response = render_to_response('professors/index.html', context)
    return response


def professors_detail(request, pk):
    context = {

    }
    response = render_to_response('professors/detail.html', context)
    return response
