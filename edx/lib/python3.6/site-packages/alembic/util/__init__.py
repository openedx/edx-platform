from .langhelpers import (  # noqa
    asbool, rev_id, to_tuple, to_list, memoized_property, dedupe_tuple,
    immutabledict, _with_legacy_names, Dispatcher, ModuleClsProxy)
from .messaging import (  # noqa
    write_outstream, status, err, obfuscate_url_pw, warn, msg, format_as_comma)
from .pyfiles import (  # noqa
    template_to_file, coerce_resource_to_filename,
    pyc_file_from_path, load_python_file, edit)
from .sqla_compat import (  # noqa
    sqla_09, sqla_092, sqla_094, sqla_099, sqla_100, sqla_105, sqla_110, sqla_1010,
    sqla_1014, sqla_1115)
from .exc import CommandError


if not sqla_09:
    raise CommandError(
        "SQLAlchemy 0.9.0 or greater is required. ")
