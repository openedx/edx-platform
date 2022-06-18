# Copyright 2010 New Relic, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

_head_re = re.compile(b"<head[^>]*>", re.IGNORECASE)

_xua_meta_re = re.compile(
    b"""<\\s*meta[^>]+http-equiv\\s*=\\s*['"]""" b"""x-ua-compatible['"][^>]*>""",
    re.IGNORECASE,
)

_charset_meta_re = re.compile(b"""<\\s*meta[^>]+charset\\s*=[^>]*>""", re.IGNORECASE)

_attachment_meta_re = re.compile(
    b"""<\\s*meta[^>]+http-equiv\\s*=\\s*['"]"""
    b"""content-disposition['"][^>]*content\\s*=\\s*(?P<quote>['"])"""
    b"""\\s*attachment(\\s*;[^>]*)?(?P=quote)[^>]*>""",
    re.IGNORECASE,
)

_body_re = re.compile(b"<body[^>]*>", re.IGNORECASE)


def insert_html_snippet(data, html_to_be_inserted, search_limit=64 * 1024):
    # First determine if we have a body tag. If we don't we
    # always give up even though strictly speaking we may not
    # actually need it to exist. This is to ensure that we have
    # all the HTML needed to perform the match correctly. In
    # doing this initial search, we only do up to the specified
    # search limit.

    body = _body_re.search(data[:search_limit])

    if not body:
        return data if len(data) > search_limit else None

    # We are definitely doing to insert something now, so
    # generate the text to be inserted. Bail out if is empty but
    # return the data to indicate we did insert something.

    text = html_to_be_inserted()

    if not text:
        return data

    # We are now going to split out everything before the body
    # to limit searches when applying the regex patterns. We
    # could have just used up to the search limit, but the
    # patterns which follow seem to be expensive enough that a
    # short a string as possible helps.

    start = body.start()
    tail, data = data[start:], data[:start]

    def insert_at_index(index):
        return b"".join((data[:index], text, data[index:], tail))

    # Search for instance of a content disposition meta tag
    # indicating that the response is actually being served up
    # as an attachment and would be saved as a file and not
    # actually interpreted by a browser.

    if _attachment_meta_re.search(data):
        return data + tail

    # Search for instances of X-UA or charset meta tags. We will
    # use whichever is the last to appear in the data.

    xua_meta = _xua_meta_re.search(data)
    charset_meta = _charset_meta_re.search(data)

    index = max(
        xua_meta and xua_meta.end() or 0, charset_meta and charset_meta.end() or 0
    )

    if index:
        return insert_at_index(index)

    # Next try for the start of head section.

    head = _head_re.search(data)

    if head:
        return insert_at_index(head.end())

    # Finally if no joy, insert before the start of the body.

    return insert_at_index(body.start())


def verify_body_exists(data):
    return _body_re.search(data)
