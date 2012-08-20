from django.core.urlresolvers import reverse
from mitxmako.shortcuts import render_to_string
from utils import *
from mustache_helpers import mustache_helpers
from functools import partial

import pystache_custom as pystache
import urllib

def pluralize(singular_term, count):
    if int(count) >= 2:
        return singular_term + 's'
    return singular_term

def show_if(text, condition):
    if condition:
        return text
    else:
        return ''

def render_content(content, additional_context={}):
    content_info = {
        'displayed_title': content.get('highlighted_title') or content.get('title', ''),
        'displayed_body': content.get('highlighted_body') or content.get('body', ''),
        'raw_tags': ','.join(content.get('tags', [])),
    }
    context = {
        'content': merge_dict(content, content_info),
        content['type']: True,
    }
    context = merge_dict(context, additional_context)
    partial_mustache_helpers = {k: partial(v, content) for k, v in mustache_helpers.items()}
    context = merge_dict(context, partial_mustache_helpers)
    return render_mustache('discussion/_content.mustache', context)
