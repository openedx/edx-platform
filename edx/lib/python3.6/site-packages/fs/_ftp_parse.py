from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import unicodedata
import datetime
import re
import time

from pytz import UTC

from .enums import ResourceType
from .permissions import Permissions


epoch_dt = datetime.datetime.fromtimestamp(0, UTC)


re_linux = re.compile(
    """
    ^
    ([ldrwx-]{10})
    \s+?
    (\d+)
    \s+?
    ([\w\-]+)
    \s+?
    ([\w\-]+)
    \s+?
    (\d+)
    \s+?
    (\w{3}\s+\d{1,2}\s+[\w:]+)
    \s+
    (.*?)
    $
    """,
    re.VERBOSE,
)


def get_decoders():
    decoders = [(re_linux, decode_linux)]
    return decoders


def parse(lines):
    info = []
    for line in lines:
        if not line.strip():
            continue
        raw_info = parse_line(line)
        if raw_info is not None:
            info.append(raw_info)
    return info


def parse_line(line):
    for line_re, decode_callable in get_decoders():
        match = line_re.match(line)
        if match is not None:
            return decode_callable(line, match)
    return None


def _parse_time(t):
    t = " ".join(token.strip() for token in t.lower().split(" "))
    try:
        try:
            _t = time.strptime(t, "%b %d %Y")
        except ValueError:
            _t = time.strptime(t, "%b %d %H:%M")
    except ValueError:
        # Unknown time format
        return None

    year = _t.tm_year if _t.tm_year != 1900 else time.localtime().tm_year
    month = _t.tm_mon
    day = _t.tm_mday
    hour = _t.tm_hour
    minutes = _t.tm_min
    dt = datetime.datetime(year, month, day, hour, minutes, tzinfo=UTC)

    epoch_time = (dt - epoch_dt).total_seconds()
    return epoch_time


def decode_linux(line, match):
    perms, links, uid, gid, size, mtime, name = match.groups()
    is_link = perms.startswith("l")
    is_dir = perms.startswith("d") or is_link
    if is_link:
        name, _, _link_name = name.partition("->")
        name = name.strip()
        _link_name = _link_name.strip()
    permissions = Permissions.parse(perms[1:])

    mtime_epoch = _parse_time(mtime)

    name = unicodedata.normalize("NFC", name)

    raw_info = {
        "basic": {"name": name, "is_dir": is_dir},
        "details": {
            "size": int(size),
            "type": int(ResourceType.directory if is_dir else ResourceType.file),
        },
        "access": {"permissions": permissions.dump()},
        "ftp": {"ls": line},
    }
    access = raw_info["access"]
    details = raw_info["details"]
    if mtime_epoch is not None:
        details["modified"] = mtime_epoch

    access["user"] = uid
    access["group"] = gid

    return raw_info
