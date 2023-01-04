# /usr/bin/env python
"""
This module has utility functions for gathering up the static content
that is defined by XModules and XModuleDescriptors (javascript and css)
"""


import errno
import hashlib
import json
import logging
import os
import sys
import textwrap
from collections import defaultdict
from pkg_resources import resource_string

import django
from docopt import docopt
from path import Path as path

from xmodule.annotatable_block import AnnotatableBlock
from xmodule.capa_block import ProblemBlock
from xmodule.conditional_block import ConditionalBlock
from xmodule.html_block import AboutBlock, CourseInfoBlock, HtmlBlock, StaticTabBlock
from xmodule.library_content_block import LibraryContentBlock
from xmodule.lti_block import LTIBlock
from xmodule.poll_block import PollBlock
from xmodule.seq_block import SequenceBlock
from xmodule.split_test_block import SplitTestBlock
from xmodule.template_block import CustomTagBlock
from xmodule.word_cloud_block import WordCloudBlock
from xmodule.x_module import HTMLSnippet

LOG = logging.getLogger(__name__)


class VideoBlock(HTMLSnippet):  # lint-amnesty, pylint: disable=abstract-method
    """
    Static assets for VideoBlock.
    Kept here because importing VideoBlock code requires Django to be setup.
    """

    preview_view_js = {
        'js': [
            resource_string(__name__, 'js/src/video/10_main.js'),
        ],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js')
    }
    preview_view_css = {
        'scss': [
            resource_string(__name__, 'css/video/display.scss'),
            resource_string(__name__, 'css/video/accessible_menu.scss'),
        ],
    }

    studio_view_js = {
        'js': [
            resource_string(__name__, 'js/src/tabs/tabs-aggregator.js'),
        ],
        'xmodule_js': resource_string(__name__, 'js/src/xmodule.js'),
    }

    studio_view_css = {
        'scss': [
            resource_string(__name__, 'css/tabs/tabs.scss'),
        ]
    }


# List of XBlocks which use this static content setup.
# Should only be used for XModules being converted to XBlocks.
XBLOCK_CLASSES = [
    AboutBlock,
    AnnotatableBlock,
    ConditionalBlock,
    CourseInfoBlock,
    CustomTagBlock,
    HtmlBlock,
    LibraryContentBlock,
    LTIBlock,
    PollBlock,
    ProblemBlock,
    SequenceBlock,
    SplitTestBlock,
    StaticTabBlock,
    VideoBlock,
    WordCloudBlock,
]


def write_module_styles(output_root):
    """Write all registered XModule css, sass, and scss files to output root."""
    return _write_styles('.xmodule_display', output_root, XBLOCK_CLASSES, 'get_preview_view_css')


def write_module_js(output_root):
    """Write all registered XModule js and coffee files to output root."""
    return _write_js(output_root, XBLOCK_CLASSES, 'get_preview_view_js')


def write_descriptor_styles(output_root):
    """Write all registered XModuleDescriptor css, sass, and scss files to output root."""
    return _write_styles('.xmodule_edit', output_root, XBLOCK_CLASSES, 'get_studio_view_css')


def write_descriptor_js(output_root):
    """Write all registered XModuleDescriptor js and coffee files to output root."""
    return _write_js(output_root, XBLOCK_CLASSES, 'get_studio_view_js')


def _ensure_dir(directory):
    """Ensure that `directory` exists."""
    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def _write_styles(selector, output_root, classes, css_attribute):
    """
    Write the css fragments from all XModules in `classes`
    into `output_root` as individual files, hashed by the contents to remove
    duplicates
    """
    contents = {}

    css_fragments = defaultdict(set)
    for class_ in classes:
        class_css = getattr(class_, css_attribute)()
        for filetype in ('sass', 'scss', 'css'):
            for idx, fragment in enumerate(class_css.get(filetype, [])):
                css_fragments[idx, filetype, fragment].add(class_.__name__)
    css_imports = defaultdict(set)
    for (idx, filetype, fragment), classes in sorted(css_fragments.items()):  # lint-amnesty, pylint: disable=redefined-argument-from-local
        fragment_name = "{idx:0=3d}-{hash}.{type}".format(
            idx=idx,
            hash=hashlib.md5(fragment).hexdigest(),
            type=filetype)
        # Prepend _ so that sass just includes the files into a single file
        filename = '_' + fragment_name
        contents[filename] = fragment

        for class_ in classes:
            css_imports[class_].add(fragment_name)

    module_styles_lines = [
        "@import 'bourbon/bourbon';",
        "@import 'lms/theme/variables';",
    ]
    for class_, fragment_names in sorted(css_imports.items()):
        fragment_names = sorted(fragment_names)
        module_styles_lines.append("""{selector}.xmodule_{class_} {{""".format(
            class_=class_, selector=selector
        ))
        module_styles_lines.extend(f'  @import "{name}";' for name in fragment_names)
        module_styles_lines.append('}')

    contents['_module-styles.scss'] = '\n'.join(module_styles_lines)

    _write_files(output_root, contents)


def _write_js(output_root, classes, js_attribute):
    """
    Write the javascript fragments from all XModules in `classes`
    into `output_root` as individual files, hashed by the contents to remove
    duplicates

    Returns a dictionary mapping class names to the files that they depend on.
    """
    file_contents = {}
    file_owners = defaultdict(list)

    fragment_owners = defaultdict(list)
    for class_ in classes:
        module_js = getattr(class_, js_attribute)()
        # It will enforce 000 prefix for xmodule.js.
        fragment_owners[(0, 'js', module_js.get('xmodule_js'))].append(getattr(class_, js_attribute + '_bundle_name')())
        for filetype in ('coffee', 'js'):
            for idx, fragment in enumerate(module_js.get(filetype, [])):
                fragment_owners[(idx + 1, filetype, fragment)].append(getattr(class_, js_attribute + '_bundle_name')())

    for (idx, filetype, fragment), owners in sorted(fragment_owners.items()):
        filename = "{idx:0=3d}-{hash}.{type}".format(
            idx=idx,
            hash=hashlib.md5(fragment).hexdigest(),
            type=filetype)
        file_contents[filename] = fragment
        for owner in owners:
            file_owners[owner].append(output_root / filename)

    _write_files(output_root, file_contents, {'.coffee': '.js'})

    return file_owners


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
    to_delete = {file.basename() for file in output_root.files()} - set(contents.keys())

    if generated_suffix_map:
        for output_file in contents.keys():
            for suffix, generated_suffix in generated_suffix_map.items():
                if output_file.endswith(suffix):
                    to_delete.discard(output_file.replace(suffix, generated_suffix))

    for extra_file in to_delete:
        (output_root / extra_file).remove_p()

    for filename, file_content in contents.items():
        output_file = output_root / filename

        not_file = not output_file.isfile()

        # Sometimes content is already unicode and sometimes it's not
        # so we add this conditional here to make sure that below we're
        # always working with streams of bytes.
        if not isinstance(file_content, bytes):
            file_content = file_content.encode('utf-8')

        # not_file is included to short-circuit this check, because
        # read_md5 depends on the file already existing
        write_file = not_file or output_file.read_md5() != hashlib.md5(file_content).digest()
        if write_file:
            LOG.debug("Writing %s", output_file)
            output_file.write_bytes(file_content)
        else:
            LOG.debug("%s unchanged, skipping", output_file)


def write_webpack(output_file, module_files, descriptor_files):
    """
    Write all xmodule and xmodule descriptor javascript into module-specific bundles.

    The output format should be suitable for smart-merging into an existing webpack configuration.
    """
    _ensure_dir(output_file.dirname())

    config = {
        'entry': {}
    }
    for (owner, files) in list(module_files.items()) + list(descriptor_files.items()):
        unique_files = sorted({f'./{file}' for file in files})
        if len(unique_files) == 1:
            unique_files = unique_files[0]
        config['entry'][owner] = unique_files
    # config['entry']['modules/js/all'] = sorted(set('./{}'.format(file) for file in sum(module_files.values(), [])))
    # config['entry']['descriptors/js/all'] = sorted(set('./{}'.format(file) for file in sum(descriptor_files.values(), [])))  # lint-amnesty, pylint: disable=line-too-long

    with output_file.open('w') as outfile:
        outfile.write(
            textwrap.dedent("""\
                module.exports = {config_json};
            """).format(
                config_json=json.dumps(
                    config,
                    indent=4,
                    sort_keys=True,
                )
            )
        )


def main():
    """
    Generate
    Usage: static_content.py <output_root>
    """
    from django.conf import settings
    # Install only the apps whose models are imported when this runs
    installed_apps = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'config_models',
        'openedx.core.djangoapps.video_config',
        'openedx.core.djangoapps.video_pipeline',
    )
    try:
        import edxval  # lint-amnesty, pylint: disable=unused-import
        installed_apps += ('edxval',)
    except ImportError:
        pass
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=installed_apps,
        )
    django.setup()

    args = docopt(main.__doc__)
    root = path(args['<output_root>'])

    descriptor_files = write_descriptor_js(root / 'descriptors/js')
    write_descriptor_styles(root / 'descriptors/css')
    module_files = write_module_js(root / 'modules/js')
    write_module_styles(root / 'modules/css')
    write_webpack(root / 'webpack.xmodule.config.js', module_files, descriptor_files)


if __name__ == '__main__':
    sys.exit(main())
