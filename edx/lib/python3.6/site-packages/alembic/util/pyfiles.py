import sys
import os
import re
from .compat import load_module_py, load_module_pyc, \
    get_current_bytecode_suffixes, has_pep3147
from mako.template import Template
from mako import exceptions
import tempfile
from .exc import CommandError


def template_to_file(template_file, dest, output_encoding, **kw):
    template = Template(filename=template_file)
    try:
        output = template.render_unicode(**kw).encode(output_encoding)
    except:
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as ntf:
            ntf.write(
                exceptions.text_error_template().
                render_unicode().encode(output_encoding))
            fname = ntf.name
        raise CommandError(
            "Template rendering failed; see %s for a "
            "template-oriented traceback." % fname)
    else:
        with open(dest, 'wb') as f:
            f.write(output)


def coerce_resource_to_filename(fname):
    """Interpret a filename as either a filesystem location or as a package
    resource.

    Names that are non absolute paths and contain a colon
    are interpreted as resources and coerced to a file location.

    """
    if not os.path.isabs(fname) and ":" in fname:
        import pkg_resources
        fname = pkg_resources.resource_filename(*fname.split(':'))
    return fname


def pyc_file_from_path(path):
    """Given a python source path, locate the .pyc.

    """

    if has_pep3147():
        import imp
        candidate = imp.cache_from_source(path)
        if os.path.exists(candidate):
            return candidate

    filepath, ext = os.path.splitext(path)
    for ext in get_current_bytecode_suffixes():
        if os.path.exists(filepath + ext):
            return filepath + ext
    else:
        return None


def edit(path):
    """Given a source path, run the EDITOR for it"""

    import editor
    try:
        editor.edit(path)
    except Exception as exc:
        raise CommandError('Error executing editor (%s)' % (exc,))


def load_python_file(dir_, filename):
    """Load a file from the given path as a Python module."""

    module_id = re.sub(r'\W', "_", filename)
    path = os.path.join(dir_, filename)
    _, ext = os.path.splitext(filename)
    if ext == ".py":
        if os.path.exists(path):
            module = load_module_py(module_id, path)
        else:
            pyc_path = pyc_file_from_path(path)
            if pyc_path is None:
                raise ImportError("Can't find Python file %s" % path)
            else:
                module = load_module_pyc(module_id, pyc_path)
    elif ext in (".pyc", ".pyo"):
        module = load_module_pyc(module_id, path)
    return module
