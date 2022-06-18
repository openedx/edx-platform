#binstar client influence/copy of cli mechanisms

MODULE_EXTENSIONS = ('.py', '.pyc', '.pyo')
import pkgutil
from os.path import dirname

def sub_command_names():
    return [name for _, name, _ in pkgutil.iter_modules([dirname(__file__)]) if not name.startswith('_')]

def sub_commands():
    names = sub_command_names()
    this_module = __import__(__package__, fromlist=names)
    for name in names:
        yield getattr(this_module, name)