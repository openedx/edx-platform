import pkg_resources

from mako.template import Template

def render_template(template_name, context):
    return Template(
        pkg_resources.resource_string(__name__, 'html_templates/%s' % template_name),
        module_directory='/tmp/xmodule_mako',
    ).render(**context)