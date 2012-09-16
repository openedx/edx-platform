from django.core.urlresolvers import reverse
from django.conf import settings
from mitxmako.shortcuts import render_to_string
from mustache_helpers import mustache_helpers
from django.core.urlresolvers import reverse
from functools import partial

from utils import *
import django_comment_client.settings as cc_settings

import pystache_custom as pystache
import urllib
import os

def pluralize(singular_term, count):
    if int(count) >= 2 or int(count) == 0:
        return singular_term + 's'
    return singular_term

# TODO there should be a better way to handle this
def include_mustache_templates():
    mustache_dir = settings.PROJECT_ROOT / 'templates' / 'discussion' / 'mustache'
    valid_file_name = lambda file_name: file_name.endswith('.mustache')
    read_file = lambda file_name: (file_name, open(mustache_dir / file_name, "r").read())
    strip_file_name = lambda x: (x[0].rpartition('.')[0], x[1])
    wrap_in_tag = lambda x: "<script type='text/template' id='{0}'>{1}</script>".format(x[0], x[1])

    file_contents = map(read_file, filter(valid_file_name, os.listdir(mustache_dir)))
    return '\n'.join(map(wrap_in_tag, map(strip_file_name, file_contents)))

def render_content(content, additional_context={}):

    context = {
        'content': extend_content(content),
        content['type']: True,
    }
    if cc_settings.MAX_COMMENT_DEPTH is not None:
        if content['type'] == 'thread':
            if cc_settings.MAX_COMMENT_DEPTH < 0:
                context['max_depth'] = True
        elif content['type'] == 'comment':
            if cc_settings.MAX_COMMENT_DEPTH <= content['depth']:
                context['max_depth'] = True
    context = merge_dict(context, additional_context)
    partial_mustache_helpers = {k: partial(v, content) for k, v in mustache_helpers.items()}
    context = merge_dict(context, partial_mustache_helpers)
    return render_mustache('discussion/mustache/_content.mustache', context)
