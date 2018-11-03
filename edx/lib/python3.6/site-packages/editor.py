#!/usr/bin/env python
"""Tools for invoking editors programmatically."""

from __future__ import print_function

import sys
import locale
import os.path
import subprocess
import tempfile
from distutils.spawn import find_executable


__all__ = [
    'edit',
    'get_editor',
    'EditorError',
]

__version__ = '1.0.3'


class EditorError(RuntimeError):
    pass


def get_default_editors():
    # TODO: Make platform-specific
    return [
        'editor',
        'vim',
        'emacs',
        'nano',
    ]


def get_editor_args(editor):
    if editor in ['vim', 'gvim', 'vim.basic', 'vim.tiny']:
        return ['-f', '-o']

    elif editor == 'emacs':
        return ['-nw']

    elif editor == 'gedit':
        return ['-w', '--new-window']

    elif editor == 'nano':
        return ['-R']

    else:
        return []


def get_editor():
    # Get the editor from the environment.  Prefer VISUAL to EDITOR
    editor = os.environ.get('VISUAL') or os.environ.get('EDITOR')
    if editor:
        return editor

    # None found in the environment.  Fallback to platform-specific defaults.
    for ed in get_default_editors():
        path = find_executable(ed)
        if path is not None:
            return path

    raise EditorError("Unable to find a viable editor on this system."
        "Please consider setting your $EDITOR variable")


def get_tty_filename():
    if sys.platform == 'win32':
        return 'CON:'
    return '/dev/tty'


def edit(filename=None, contents=None, use_tty=None):
    editor = get_editor()
    args = [editor] + get_editor_args(os.path.basename(os.path.realpath(editor)))

    if use_tty is None:
        use_tty = sys.stdin.isatty() and not sys.stdout.isatty()

    if filename is None:
        tmp = tempfile.NamedTemporaryFile()
        filename = tmp.name

    if contents is not None:
        with open(filename, mode='wb') as f:
            f.write(contents)

    args += [filename]

    stdout = None
    if use_tty:
        stdout = open(get_tty_filename(), 'wb')

    proc = subprocess.Popen(args, close_fds=True, stdout=stdout)
    proc.communicate()

    with open(filename, mode='rb') as f:
        return f.read()


def _get_editor(ns):
    print(get_editor())


def _edit(ns):
    contents = ns.contents
    if contents is not None:
        contents = contents.encode(locale.getpreferredencoding())
    print(edit(filename=ns.path, contents=contents))


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers()

    cmd = sp.add_parser('get-editor')
    cmd.set_defaults(cmd=_get_editor)

    cmd = sp.add_parser('edit')
    cmd.set_defaults(cmd=_edit)
    cmd.add_argument('path', type=str, nargs='?')
    cmd.add_argument('--contents', type=str)

    ns = ap.parse_args()
    ns.cmd(ns)
