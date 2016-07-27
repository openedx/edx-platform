"""
Utils for Discussion XBlock and Course Discussion XBlock
"""

import os

from django.templatetags.static import static

from mako.template import Template as MakoTemplate

from path import Path as path


JS_URLS = [
    # VENDOR
    'js/vendor/mustache.js',

    # FIXME: Provides gettext, ngettext, interpolate; these are probably already available?
    'xblock/discussion/js/vendor/i18n.js',
]


def _(text):
    """
    A noop underscore function that marks strings for extraction.
    """
    return text


def render_mustache_templates():
    """ Renders all mustache templates as script tags """
    mustache_dir = path(__file__).abspath().dirname() / 'templates' / 'mustache'

    def is_valid_file_name(file_name):
        """ Checks if file is a mustache template """
        return file_name.endswith('.mustache')

    def read_file(file_name):
        """ Reads file and decodes it's content """
        return (mustache_dir / file_name).text("utf-8")

    def template_id_from_file_name(file_name):
        """ Generates template_id from file name """
        return file_name.rpartition('.')[0]

    def process_mako(template_content):
        """ Creates and renders Mako template """
        return MakoTemplate(template_content).render_unicode()

    def make_script_tag(script_id, content):
        """ Wraps content in script tag """
        return u"<script type='text/template' id='{0}'>{1}</script>".format(script_id, content)

    return u'\n'.join(
        make_script_tag(template_id_from_file_name(file_name), process_mako(read_file(file_name)))
        for file_name in os.listdir(mustache_dir)
        if is_valid_file_name(file_name)
    )


def add_resources_to_fragment(fragment):
    """
    Add resources specified in JS_URLS to a given fragment.
    """
    for url in JS_URLS:
        fragment.add_javascript_url(asset_to_static_url(url))


def asset_to_static_url(asset_path):
    """
    :param str asset_path: path to asset
    :return: str|unicode url of asset
    """
    return static(asset_path)
