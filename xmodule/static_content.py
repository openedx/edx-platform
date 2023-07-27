# /usr/bin/env python
"""
Generate <output_root>/webpack.xmodule.config.js, with a display & editor Webpack bundle for each builtin block.

It looks like this:

  module.exports = {
      "entry": {
          "AboutBlockDisplay": [
              "./xmodule/js/src/xmodule.js",
              "./xmodule/js/src/html/display.js",
              "./xmodule/js/src/javascript_loader.js",
              "./xmodule/js/src/collapsible.js",
              "./xmodule/js/src/html/imageModal.js",
              "./xmodule/js/common_static/js/vendor/draggabilly.js"
          ],
          "AboutBlockEditor": [
              "./xmodule/js/src/xmodule.js",
              "./xmodule/js/src/html/edit.js"
          ],
          "AnnotatableBlockDisplay": [
              "./xmodule/js/src/xmodule.js",
              "./xmodule/js/src/html/display.js",
              "./xmodule/js/src/annotatable/display.js",
              "./xmodule/js/src/javascript_loader.js",
              "./xmodule/js/src/collapsible.js"
          ],
          ... etc.
      }
  }

Don't add to this! It will soon be removed as part of: https://github.com/openedx/edx-platform/issues/32481
"""


import errno
import json
import logging
import os
import sys
import textwrap
from pkg_resources import resource_filename

import django
from pathlib import Path as path

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


def _ensure_dir(directory):
    """Ensure that `directory` exists."""
    try:
        os.makedirs(directory)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def write_webpack(output_file, module_files, descriptor_files):
    """
    Write all xmodule and xmodule descriptor javascript into module-specific bundles.

    The output format should be suitable for smart-merging into an existing webpack configuration.
    """
    _ensure_dir(output_file.parent)

    config = {
        'entry': {}
    }
    for (owner, unique_files) in list(module_files.items()) + list(descriptor_files.items()):
        if len(unique_files) == 1:
            unique_files = unique_files[0]
        config['entry'][owner] = unique_files
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
    Generate the weback config.

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

    try:
        root = path(sys.argv[1])
    except IndexError:
        sys.exit(main.__doc__)

    # We assume this module is located at edx-platform/xmodule/static_content.py.
    # Not the most robust assumption, but this script will be gone soon.
    repo_root = path(__file__).parent.parent

    module_files = {
        class_.get_preview_view_js_bundle_name(): [
            "./" + str(path(fragment_path).relative_to(repo_root))
            for fragment_path in [
                class_.get_preview_view_js()['xmodule_js'],
                *class_.get_preview_view_js().get('js', []),
            ]
        ]
        for class_ in XBLOCK_CLASSES
    }
    descriptor_files = {
        class_.get_studio_view_js_bundle_name(): [
            "./" + str(path(fragment_path).relative_to(repo_root))
            for fragment_path in [
                class_.get_studio_view_js()['xmodule_js'],
                *class_.get_studio_view_js().get('js', []),
            ]
        ]
        for class_ in XBLOCK_CLASSES
    }
    write_webpack(root / 'webpack.xmodule.config.js', module_files, descriptor_files)


if __name__ == '__main__':
    sys.exit(main())
