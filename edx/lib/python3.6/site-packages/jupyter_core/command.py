"""The root `jupyter` command.

This does nothing other than dispatch to subcommands or output path info.
"""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from __future__ import print_function

import argparse
import errno
import json
import os
import sys
from subprocess import Popen

from . import paths
from .version import __version__

class JupyterParser(argparse.ArgumentParser):
    
    @property
    def epilog(self):
        """Add subcommands to epilog on request
        
        Avoids searching PATH for subcommands unless help output is requested.
        """
        return 'Available subcommands: %s' % ' '.join(list_subcommands())
    
    @epilog.setter
    def epilog(self, x):
        """Ignore epilog set in Parser.__init__"""
        pass

def jupyter_parser():
    parser = JupyterParser(
        description="Jupyter: Interactive Computing",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    # don't use argparse's version action because it prints to stderr on py2
    group.add_argument('--version', action='store_true',
        help="show the jupyter command's version and exit")
    group.add_argument('subcommand', type=str, nargs='?', help='the subcommand to launch')
    
    group.add_argument('--config-dir', action='store_true',
        help="show Jupyter config dir")
    group.add_argument('--data-dir', action='store_true',
        help="show Jupyter data dir")
    group.add_argument('--runtime-dir', action='store_true',
        help="show Jupyter runtime dir")
    group.add_argument('--paths', action='store_true',
        help="show all Jupyter paths. Add --json for machine-readable format.")
    parser.add_argument('--json', action='store_true',
        help="output paths as machine-readable json")
    
    return parser


def list_subcommands():
    """List all jupyter subcommands
    
    searches PATH for `jupyter-name`
    
    Returns a list of jupyter's subcommand names, without the `jupyter-` prefix.
    Nested children (e.g. jupyter-sub-subsub) are not included.
    """
    subcommand_tuples = set()
    # construct a set of `('foo', 'bar') from `jupyter-foo-bar`
    for d in _path_with_self():
        try:
            names = os.listdir(d)
        except OSError:
            continue
        for name in names:
            if name.startswith('jupyter-'):
                if sys.platform.startswith('win'):
                    # remove file-extension on Windows
                    name = os.path.splitext(name)[0]
                subcommand_tuples.add(tuple(name.split('-')[1:]))
    # build a set of subcommand strings, excluding subcommands whose parents are defined
    subcommands = set()
    # Only include `jupyter-foo-bar` if `jupyter-foo` is not already present
    for sub_tup in subcommand_tuples:
        if not any(sub_tup[:i] in subcommand_tuples for i in range(1, len(sub_tup))):
            subcommands.add('-'.join(sub_tup))
    return sorted(subcommands)


def _execvp(cmd, argv):
    """execvp, except on Windows where it uses Popen
    
    Python provides execvp on Windows, but its behavior is problematic (Python bug#9148).
    """
    if sys.platform.startswith('win'):
        # PATH is ignored when shell=False,
        # so rely on shutil.which
        try:
            from shutil import which
        except ImportError:
            from .utils.shutil_which import which
        cmd_path = which(cmd)
        if cmd_path is None:
            raise OSError('%r not found' % cmd, errno.ENOENT)
        p = Popen([cmd_path] + argv[1:])
        # Don't raise KeyboardInterrupt in the parent process.
        # Set this after spawning, to avoid subprocess inheriting handler.
        import signal
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        p.wait()
        sys.exit(p.returncode)
    else:
        os.execvp(cmd, argv)


def _path_with_self():
    """Put `jupyter`'s dir at the front of PATH
    
    Ensures that /path/to/jupyter subcommand
    will do /path/to/jupyter-subcommand
    even if /other/jupyter-subcommand is ahead of it on PATH
    """
    scripts = [sys.argv[0]]
    if os.path.islink(scripts[0]):
        # include realpath, if `jupyter` is a symlink
        scripts.append(os.path.realpath(scripts[0]))

    path_list = (os.environ.get('PATH') or os.defpath).split(os.pathsep)
    for script in scripts:
        bindir = os.path.dirname(script)
        if (os.path.isdir(bindir)
            and os.access(script, os.X_OK) # only if it's a script
        ):
            # ensure executable's dir is on PATH
            # avoids missing subcommands when jupyter is run via absolute path
            path_list.insert(0, bindir)
    os.environ['PATH'] = os.pathsep.join(path_list)
    return path_list


def main():
    _path_with_self() # ensure executable is on PATH
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        # Don't parse if a subcommand is given
        # Avoids argparse gobbling up args passed to subcommand, such as `-h`.
        subcommand = sys.argv[1]
    else:
        parser = jupyter_parser()
        args, opts = parser.parse_known_args()
        subcommand = args.subcommand
        if args.version:
            print(__version__)
            return
        if args.json and not args.paths:
            sys.exit("--json is only used with --paths")
        if args.config_dir:
            print(paths.jupyter_config_dir())
            return
        if args.data_dir:
            print(paths.jupyter_data_dir())
            return
        if args.runtime_dir:
            print(paths.jupyter_runtime_dir())
            return
        if args.paths:
            data = {}
            data['runtime'] = [paths.jupyter_runtime_dir()]
            data['config'] = paths.jupyter_config_path()
            data['data'] = paths.jupyter_path()
            if args.json:
                print(json.dumps(data))
            else:
                for name in sorted(data):
                    path = data[name]
                    print('%s:' % name)
                    for p in path:
                        print('    ' + p)
            return
    
    if not subcommand:
        parser.print_usage(file=sys.stderr)
        sys.exit("subcommand is required")
    
    command = 'jupyter-' + subcommand
    try:
        _execvp(command, sys.argv[1:])
    except OSError as e:
        sys.exit("Error executing Jupyter command %r: %s" % (subcommand, e))


if __name__ == '__main__':
    main()
