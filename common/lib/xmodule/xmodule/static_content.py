"""
This module has utility functions for gathering up the static content
that is defined by XModules and XModuleDescriptors (javascript and css)
"""

import hashlib
import os
import errno
from collections import defaultdict

from .x_module import XModuleDescriptor


def write_module_styles(output_root, extra_descriptors):
    return _write_styles(output_root, _list_modules(extra_descriptors))


def write_module_js(output_root, extra_descriptors):
    return _write_js(output_root, _list_modules(extra_descriptors))


def write_descriptor_styles(output_root, extra_descriptors):
    return _write_styles(output_root, _list_descriptors(extra_descriptors))


def write_descriptor_js(output_root, extra_descriptors):
    return _write_js(output_root, _list_descriptors(extra_descriptors))


def _list_descriptors(extra_descriptors):
    return [
        desc for desc in [
            desc for (_, desc) in XModuleDescriptor.load_classes()
        ] + extra_descriptors
    ]


def _list_modules(extra_descriptors):
    return [
        desc.module_class
        for desc
        in _list_descriptors(extra_descriptors)
    ]


def _ensure_dir(dir_):
    try:
        os.makedirs(dir_)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def _write_styles(output_root, classes):
    _ensure_dir(output_root)

    css_fragments = defaultdict(set)
    for class_ in classes:
        class_css = class_.get_css()
        for filetype in ('sass', 'scss', 'css'):
            for idx, fragment in enumerate(class_css.get(filetype, [])):
                css_fragments[idx, filetype, fragment].add(class_.__name__)
    css_imports = defaultdict(set)
    for (idx, filetype, fragment), classes in sorted(css_fragments.items()):
        fragment_name = "{idx}-{hash}.{type}".format(
            idx=idx,
            hash=hashlib.md5(fragment).hexdigest(),
            type=filetype)
        # Prepend _ so that sass just includes the files into a single file
        with open(output_root / '_' + fragment_name, 'w') as css_file:
            css_file.write(fragment)

        for class_ in classes:
            css_imports[class_].add(fragment_name)

    with open(output_root / '_module-styles.scss', 'w') as module_styles:
        for class_, fragment_names in css_imports.items():
            imports = "\n".join('@import "{0}";'.format(name) for name in fragment_names)
            module_styles.write(""".xmodule_{class_} {{ {imports} }}""".format(
                class_=class_, imports=imports
            ))


def _write_js(output_root, classes):
    _ensure_dir(output_root)

    js_fragments = set()
    for class_ in classes:
        module_js = class_.get_javascript()
        for filetype in ('coffee', 'js'):
            for idx, fragment in enumerate(module_js.get(filetype, [])):
                js_fragments.add((idx, filetype, fragment))

    module_js = []
    for idx, filetype, fragment in sorted(js_fragments):
        path = output_root / "{idx}-{hash}.{type}".format(
            idx=idx,
            hash=hashlib.md5(fragment).hexdigest(),
            type=filetype)
        with open(path, 'w') as js_file:
            js_file.write(fragment)

        module_js.append(path)

    return module_js
