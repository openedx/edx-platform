try:
    from staticfiles.storage import staticfiles_storage
except ImportError:
    from django.contrib.staticfiles.storage import staticfiles_storage # noqa

from mitxmako.shortcuts import render_to_string

from pipeline.conf import settings
from pipeline.packager import Packager, PackageNotFound
from pipeline.utils import guess_type

def compressed_css(package_name):
    package = settings.PIPELINE_CSS.get(package_name, {})
    if package:
        package = {package_name: package}
    packager = Packager(css_packages=package, js_packages={})

    try:
        package = packager.package_for('css', package_name)
    except PackageNotFound:
        return ''  # fail silently, do not return anything if an invalid group is specified

    if settings.PIPELINE:
        return render_css(package, package.output_filename)
    else:
        paths = packager.compile(package.paths)
        return render_individual_css(package, paths)

def render_css(package, path):
    template_name = package.template_name or "pipeline/css.html"
    context = package.extra_context
    context.update({
        'type': guess_type(path, 'text/css'),
        'url': staticfiles_storage.url(path)
    })
    return render_to_string(template_name, context)

def render_individual_css(package, paths):
    tags = [render_css(package, path) for path in paths]
    return '\n'.join(tags)


def compressed_js(package_name):
    package = settings.PIPELINE_JS.get(package_name, {})
    if package:
        package = {package_name: package}
    packager = Packager(css_packages={}, js_packages=package)

    try:
        package = packager.package_for('js', package_name)
    except PackageNotFound:
        return ''  # fail silently, do not return anything if an invalid group is specified

    if settings.PIPELINE:
        return render_js(package, package.output_filename)
    else:
        paths = packager.compile(package.paths)
        templates = packager.pack_templates(package)
        return render_individual_js(package, paths, templates)

def render_js(package, path):
    template_name = package.template_name or "pipeline/js.html"
    context = package.extra_context
    context.update({
        'type': guess_type(path, 'text/javascript'),
        'url': staticfiles_storage.url(path)
    })
    return render_to_string(template_name, context)

def render_inline_js(package, js):
    context = package.extra_context
    context.update({
        'source': js
    })
    return render_to_string("pipeline/inline_js.html", context)

def render_individual_js(package, paths, templates=None):
    tags = [render_js(package, js) for js in paths]
    if templates:
        tags.append(render_inline_js(package, templates))
    return '\n'.join(tags)
