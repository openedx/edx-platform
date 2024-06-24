"""
Utility methods for parsing/generating OLX.
"""
from __future__ import annotations

import typing as t
from abc import abstractmethod

from lxml import etree


def write_xml_to_file(root_node: etree._Element, target_file: t.IO[str]) -> None:
    """
    @@TODO docstring
    @@TODO unit tests
    """
    xml_str = etree.tostring(root_node, pretty_print=True, encoding='utf-8').decode('utf-8')
    convert_quotes = lambda: True  # @@TODO: Make this a waffle flag?
    if convert_quotes():
        xml_chars = iter(xml_str)  # @@TODO: try to optimize this by streaming xml rather than rendering xml_str?
        target_file.write("".join(_convert_attrs_to_single_quotes(xml_str)))
    else:
        target_file.write(xml_str)


def _convert_attrs_to_single_quotes(xml_chars: t.Iterator[str]) -> t.Iterable[str]:
    """
    Given a stream of chars in an XML string, convert the quoutes around attrs from double to single.

    This means exchanging double-quote escape sequences in attributes values (&quot;) for literal double quotes (").
    It also means exchanging literal single quotes (') for single-quote escape sequences (&apos;).
    Since OLX heavily uses JSON it our XML attribute values, this conversion generally nets clearner XML.

    Example:
        Before:
            <problem data="{&quot;xyz&quot;: &quot;xyz's value&quot;}">...</problem>
        After:
            <problem data='{"xyz": "xyz&apos;s value"}'>...</problem>

    ASSUMPTIONS:
    * String is valid XML based on: <@@TODO link to spec>
    * String is rendered by Python's LXML library.
    * @@TODO state other syntax assumptions
    """
    try:
        while c := next(xml_chars):

            # We're outside of any tag until we see <

            if c == "<":
                yield "<"

                # We're inside a tag: < ... >

                while c := next(xml_chars):
                    if c == ">":
                        yield ">"

                        break  # Done with the tag, back to the outside

                    elif c == "\"":

                        yield "'"  # Convert double-quote close to single-quote close

                        # We're inside an attribute value: <tagname yada=" ... ">

                        while c := next(xml_chars):
                            if c == "\"":
                                yield "'"  # Convert double-quote close to single-quote close

                                break  # Done with the attribute value, back to the tag

                            elif c == "'":

                                yield "&apos;"  # Single quote in attr --> convert to escape sequence

                            elif c == "&":

                                # We're inside an escape sequence: <tagname yada="blah &...; blah">
                                escape_code = ""
                                while c := next(xml_chars):
                                    if c == ";":
                                        break  # Done with escape sequence
                                    else:
                                        escape_code += c
                                if escape_code == "quot":
                                    yield "\""  # Escape sequence is &quot; --> convert to literal double-qoute
                                else:
                                    yield "&{escape_code};"  # Any other escape sequence --> leave it as-is

                            else:
                                yield c  # yield char from attribute value
                    else:
                        yield c  # yield char from inside a tag
            else:
                yield c  # yield char from outside tags
    except StopIteration:
        pass
