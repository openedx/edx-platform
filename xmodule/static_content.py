# /usr/bin/env python
"""
This module has utility functions for gathering up the javascript
that is defined by XModules and XModuleDescriptors
"""


import errno
import hashlib
import json
import logging
import os
import sys
import textwrap
from collections import defaultdict
from pkg_resources import resource_filename

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
            resource_filename(__name__, 'js/src/video/10_main.js'),
        ],
        'xmodule_js': resource_filename(__name__, 'js/src/xmodule.js')
    }

    studio_view_js = {
        'js': [
            resource_filename(__name__, 'js/src/tabs/tabs-aggregator.js'),
        ],
        'xmodule_js': resource_filename(__name__, 'js/src/xmodule.js'),
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


def write_module_js():
    return _write_js(XBLOCK_CLASSES, 'get_preview_view_js')


def write_descriptor_js():
    return _write_js(XBLOCK_CLASSES, 'get_studio_view_js')


def _ensure_dir(directory):
    """Ensure that `directory` exists."""
    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def _write_js(classes, js_attribute):
    """
    Returns a dictionary mapping class names to the files that they depend on.
    """
    file_owners = defaultdict(list)
    for class_ in classes:
        bundle_name = getattr(class_, js_attribute + '_bundle_name')()
        module_js = getattr(class_, js_attribute)()
        fragment_paths = [module_js['xmodule_js']] + module_js.get('js', [])
        for fragment_path in fragment_paths:
            if "/edx-platform/" not in fragment_path:
                breakpoint()
            fragment_rel_path = fragment_path.split("/edx-platform/")[-1]
            file_owners[bundle_name].append(fragment_rel_path)
    return file_owners


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
        if len(files) == 1:
            files = files[0]
        config['entry'][owner] = files

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

    descriptor_files = write_descriptor_js()
    module_files = write_module_js()
    write_webpack(root / 'webpack.xmodule.config.js', module_files, descriptor_files)


if __name__ == '__main__':
    sys.exit(main())
