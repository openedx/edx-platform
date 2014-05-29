# /usr/bin/env python
"""
This module has utility functions for gathering up the static content
that is defined by XModules and XModuleDescriptors (javascript and css)
"""

import logging
import hashlib
import os
import errno
import sys
from collections import defaultdict
from docopt import docopt
from path import path

from xmodule.x_module import XModuleDescriptor


LOG = logging.getLogger(__name__)


def write_module_styles(output_root):
    """Write all registered XModule css, sass, and scss files to output root."""
    return _write_styles('.xmodule_display', output_root, _list_modules())


def write_module_js(output_root):
    """Write all registered XModule js and coffee files to output root."""
    return _write_js(output_root, _list_modules())


def write_descriptor_styles(output_root):
    """Write all registered XModuleDescriptor css, sass, and scss files to output root."""
    return _write_styles('.xmodule_edit', output_root, _list_descriptors())


def write_descriptor_js(output_root):
    """Write all registered XModuleDescriptor js and coffee files to output root."""
    return _write_js(output_root, _list_descriptors())


def _list_descriptors():
    """Return a list of all registered XModuleDescriptor classes."""
    return [
        desc for desc in [
            desc for (_, desc) in XModuleDescriptor.load_classes()
        ]
    ]


def _list_modules():
    """Return a list of all registered XModule classes."""
    return [
        desc.module_class
        for desc
        in _list_descriptors()
    ]


def _ensure_dir(directory):
    """Ensure that `directory` exists."""
    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def _write_styles(selector, output_root, classes):
    """
    Write the css fragments from all XModules in `classes`
    into `output_root` as individual files, hashed by the contents to remove
    duplicates
    """
    contents = {}

    css_fragments = defaultdict(set)
    for class_ in classes:
        class_css = class_.get_css()
        for filetype in ('sass', 'scss', 'css'):
            for idx, fragment in enumerate(class_css.get(filetype, [])):
                css_fragments[idx, filetype, fragment].add(class_.__name__)
    css_imports = defaultdict(set)
    for (idx, filetype, fragment), classes in sorted(css_fragments.items()):
        fragment_name = "{idx:0=3d}-{hash}.{type}".format(
            idx=idx,
            hash=hashlib.md5(fragment).hexdigest(),
            type=filetype)
        # Prepend _ so that sass just includes the files into a single file
        filename = '_' + fragment_name
        contents[filename] = fragment

        for class_ in classes:
            css_imports[class_].add(fragment_name)

    module_styles_lines = []
    module_styles_lines.append("@import 'bourbon/bourbon';")
    module_styles_lines.append("@import 'bourbon/addons/button';")
    module_styles_lines.append("@import 'assets/anims';")
    module_styles_lines.append("@import 'assets/xmodule';")
    for class_, fragment_names in css_imports.items():
        module_styles_lines.append("""{selector}.xmodule_{class_} {{""".format(
            class_=class_, selector=selector
        ))
        module_styles_lines.extend('  @import "{0}";'.format(name) for name in fragment_names)
        module_styles_lines.append('}')

    contents['_module-styles.scss'] = '\n'.join(module_styles_lines)

    _write_files(output_root, contents)


def _write_js(output_root, classes):
    """
    Write the javascript fragments from all XModules in `classes`
    into `output_root` as individual files, hashed by the contents to remove
    duplicates
    """
    contents = {}

    js_fragments = set()
    for class_ in classes:
        module_js = class_.get_javascript()
        for filetype in ('coffee', 'js'):
            for idx, fragment in enumerate(module_js.get(filetype, [])):
                js_fragments.add((idx, filetype, fragment))

    for idx, filetype, fragment in sorted(js_fragments):
        filename = "{idx:0=3d}-{hash}.{type}".format(
            idx=idx,
            hash=hashlib.md5(fragment).hexdigest(),
            type=filetype)
        contents[filename] = fragment

    _write_files(output_root, contents, {'.coffee': '.js'})

    return [output_root / filename for filename in contents.keys()]


def _write_files(output_root, contents, generated_suffix_map=None):
    """
    Write file contents to output root.

    Any files not listed in contents that exists in output_root will be deleted,
    unless it matches one of the patterns in `generated_suffix_map`.

    output_root (path): The root directory to write the file contents in
    contents (dict): A map from filenames to file contents to be written to the output_root
    generated_suffix_map (dict): Optional. Maps file suffix to generated file suffix.
        For any file in contents, if the suffix matches a key in `generated_suffix_map`,
        then the same filename with the suffix replaced by the value from `generated_suffix_map`
        will be ignored
    """
    _ensure_dir(output_root)
    to_delete = set(file.basename() for file in output_root.files()) - set(contents.keys())

    if generated_suffix_map:
        for output_file in contents.keys():
            for suffix, generated_suffix in generated_suffix_map.items():
                if output_file.endswith(suffix):
                    to_delete.discard(output_file.replace(suffix, generated_suffix))

    for extra_file in to_delete:
        (output_root / extra_file).remove_p()

    for filename, file_content in contents.iteritems():
        output_file = output_root / filename

        not_file = not output_file.isfile()

        # not_file is included to short-circuit this check, because
        # read_md5 depends on the file already existing
        write_file = not_file or output_file.read_md5() != hashlib.md5(file_content).digest()  # pylint: disable=E1121
        if write_file:
            LOG.debug("Writing %s", output_file)
            output_file.write_bytes(file_content)
        else:
            LOG.debug("%s unchanged, skipping", output_file)


def main():
    """
    Generate
    Usage: static_content.py <output_root>
    """
    args = docopt(main.__doc__)
    root = path(args['<output_root>'])

    write_descriptor_js(root / 'descriptors/js')
    write_descriptor_styles(root / 'descriptors/css')
    write_module_js(root / 'modules/js')
    write_module_styles(root / 'modules/css')


if __name__ == '__main__':
    sys.exit(main())
