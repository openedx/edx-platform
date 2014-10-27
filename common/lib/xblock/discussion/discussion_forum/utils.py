import os
import pkg_resources
from django.templatetags.static import static

from edxmako.shortcuts import render_to_string
from django.template import Context, Template

from django.conf import settings

from mako.template import Template as MakoTemplate


JS_URLS = [
    # VENDOR
    'js/vendor/URI.min.js',
    'js/vendor/jquery.leanModal.min.js',
    'js/vendor/jquery.timeago.js',
    'js/vendor/underscore-min.js',
    'js/vendor/backbone-min.js',
    'js/vendor/mustache.js',
    'js/vendor/mathjax-MathJax-c9db6ac/MathJax.js?config=TeX-MML-AM_HTMLorMML-full',

    'xblock/discussion/js/vendor/split.js',
    'xblock/discussion/js/vendor/i18n.js',
    'xblock/discussion/js/vendor/Markdown.Converter.js',
    'xblock/discussion/js/vendor/Markdown.Sanitizer.js',
    'xblock/discussion/js/vendor/Markdown.Editor.js',
    'xblock/discussion/js/vendor/mathjax_delay_renderer.js',
    'xblock/discussion/js/vendor/customwmd.js',
]

CSS_URLS = [
    'xblock/discussion/css/vendor/font-awesome.css',
    'sass/discussion-forum.css',
]

main_js = u'coffee/src/discussion/main.js'
all_js = set(rooted_glob(settings.COMMON_ROOT / 'static', 'coffee/src/discussion/**/*.js'))
all_js.remove(main_js)

discussion_js = sorted(all_js) + [main_js]


def load_resource(resource_path):
    """
    Gets the content of a resource
    """
    resource_content = pkg_resources.resource_string('discussion_forum', resource_path)
    return unicode(resource_content)


def render_template(template_path, context=None):
    """
    Evaluate a template by resource path, applying the provided context
    """
    template_str = load_resource(template_path)
    template = Template(template_str)
    return template.render(Context(context or {}))


def render_mako_template(template_path, context=None):
    """
    Evaluate a mako template by resource path, applying the provided context
    """
    return render_to_string(template_path, context if context else {})


def render_mustache_templates():
    """ Renders all mustache templates as script tags """
    mustache_dir = settings.COMMON_ROOT / 'templates' / 'discussion' / 'mustache'

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


def get_scenarios_from_path(scenarios_path, include_identifier=False):
    """
    Returns an array of (title, xmlcontent) from files contained in a specified directory,
    formatted as expected for the return value of the workbench_scenarios() method
    """
    base_fullpath = os.path.dirname(os.path.realpath(__file__))
    scenarios_fullpath = os.path.join(base_fullpath, scenarios_path)

    scenarios = []
    if os.path.isdir(scenarios_fullpath):
        for template in os.listdir(scenarios_fullpath):
            if not template.endswith('.xml'):
                continue
            identifier = template[:-4]
            title = identifier.replace('_', ' ').title()
            template_path = os.path.join(scenarios_path, template)
            if not include_identifier:
                scenarios.append((title, load_resource(template_path)))
            else:
                scenarios.append((identifier, title, load_resource(template_path)))

    return scenarios


def load_scenarios_from_path(scenarios_path):
    """
    Load all xml files contained in a specified directory, as workbench scenarios
    """
    return get_scenarios_from_path(scenarios_path, include_identifier=True)


def get_js_urls():
    """ Returns a list of all additional javascript files """
    return [asset_to_static_url(path) for path in JS_URLS + discussion_js]


def get_css_urls():
    """ Returns a list of all additional css files """
    return [asset_to_static_url(path) for path in CSS_URLS]


def asset_to_static_url(asset_path):
    """
    :param str asset_path: path to asset
    :return: str|unicode url of asset
    """
    return static(asset_path)
