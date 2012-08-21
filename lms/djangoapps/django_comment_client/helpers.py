from django.core.urlresolvers import reverse
from django.template.defaultfilters import escapejs
from django.conf import settings
from mitxmako.shortcuts import render_to_string
from mustache_helpers import mustache_helpers
from functools import partial

from utils import *

import pystache_custom as pystache
import urllib
import os

def pluralize(singular_term, count):
    if int(count) >= 2:
        return singular_term + 's'
    return singular_term

def show_if(text, condition):
    if condition:
        return text
    else:
        return ''

# TODO there should be a better way to handle this
def include_mustache_templates():
    mustache_dir = settings.PROJECT_ROOT / 'templates' / 'discussion'
    valid_file_name = lambda file_name: file_name.endswith('.mustache')
    read_file = lambda file_name: (file_name, open(mustache_dir / file_name, "r").read())
    strip_file_name = lambda x: (x[0].rpartition('.')[0], x[1])
    wrap_in_tag = lambda x: "<script type='text/template' id='{0}'>{1}</script>".format(x[0], escapejs(x[1]))

    file_contents = map(read_file, filter(valid_file_name, os.listdir(mustache_dir)))
    return '\n'.join(map(wrap_in_tag, map(strip_file_name, file_contents)))



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
