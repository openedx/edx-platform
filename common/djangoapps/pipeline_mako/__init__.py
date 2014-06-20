from edxmako.shortcuts import render_to_string

from pipeline.conf import settings
from pipeline.packager import Packager
from pipeline.utils import guess_type
from static_replace import try_staticfiles_lookup


def compressed_css(package_name, raw=False):
    package = settings.PIPELINE_CSS.get(package_name, {})
    if package:
        package = {package_name: package}
    packager = Packager(css_packages=package, js_packages={})

    package = packager.package_for('css', package_name)

    if settings.PIPELINE:
        return render_css(package, package.output_filename, raw=raw)
    else:
        paths = packager.compile(package.paths)
        return render_individual_css(package, paths, raw=raw)


def render_css(package, path, raw=False):
    template_name = package.template_name or "mako/css.html"
    context = package.extra_context

    url = try_staticfiles_lookup(path)
    if raw:
        url += "?raw"
    context.update({
        'type': guess_type(path, 'text/css'),
        'url': url,
    })
    return render_to_string(template_name, context)


def render_individual_css(package, paths, raw=False):
    tags = [render_css(package, path, raw) for path in paths]
    return '\n'.join(tags)


def compressed_js(package_name):
    package = settings.PIPELINE_JS.get(package_name, {})
    if package:
        package = {package_name: package}
    packager = Packager(css_packages={}, js_packages=package)

    package = packager.package_for('js', package_name)

    if settings.PIPELINE:
        return render_js(package, package.output_filename)
    else:
        paths = packager.compile(package.paths)
        templates = packager.pack_templates(package)
        return render_individual_js(package, paths, templates)


def render_js(package, path):
    template_name = package.template_name or "mako/js.html"
    context = package.extra_context
    context.update({
        'type': guess_type(path, 'text/javascript'),
        'url': try_staticfiles_lookup(path)
    })
    return render_to_string(template_name, context)


def render_inline_js(package, js):
    context = package.extra_context
    context.update({
        'source': js
    })
    return render_to_string("mako/inline_js.html", context)


def render_individual_js(package, paths, templates=None):
    tags = [render_js(package, js) for js in paths]
    if templates:
        tags.append(render_inline_js(package, templates))
    return '\n'.join(tags)
