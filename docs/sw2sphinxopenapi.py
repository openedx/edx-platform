"""Generate ReST documents for sphinxcontrib-openapi from an OpenAPI swagger file.

This program reads an OpenAPI swagger file, and generates .rst files.  Each
file will render a segment of the swagger file, using sphinxcontrib-openapi.

An index.rst file is created listing all of the endpoints, linking to their
detailed segment page.

"""


import functools
import itertools
import os
import os.path
import re
import sys
import textwrap

import yaml


def method_ordered_items(method_data):
    """Yield the HTTP method items from method_data, in a canonical order."""
    for key in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
        if key in method_data:
            yield key, method_data[key]


def rst_header(text, level, anchor=None):
    """Create a ReST header, including a possible anchor.

    Returns a multi-line string.

    """
    rst = []
    if anchor:
        rst.append(".. _{}:".format(anchor))
        rst.append("")
    char = " #=-"[level]
    if level == 1:
        rst.append(char * len(text))
    rst.append(text)
    rst.append(char * len(text))
    rst.append("")
    return "\n".join(rst)


# Regexes that determine the segments. If one of these matches a URI, the
# matched text is the segment for that endpoint.
SEGMENTERS = [
    r"^.*?/v\d+/[\w_-]+",
    r"^(/[\w_-]+){,3}",
]


def segment_for_uri(uri):
    """Determine the segment for an endpoint's URI."""
    for segmenter in SEGMENTERS:
        m = re.search(segmenter, uri)
        if m:
            return m.group()

    return "default"


def convert_swagger_to_sphinx(swagger_file, output_dir):
    """Convert a swagger.yaml file to a series of Sphinx documents.

    Args:
        swagger_file: the filename of the OpenAPI swagger file to read.
        output_dir: the directory where the .rst files should be written.

    """
    with open(swagger_file) as swyaml:
        swagger = yaml.safe_load(swyaml)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    rel_swagger_path = os.path.relpath(swagger_file, output_dir)

    with open(os.path.join(output_dir, 'index.rst'), 'w') as index:
        pr_index = functools.partial(print, file=index)
        pr_index(rst_header(swagger['info']['title'], level=1))
        pr_index(swagger['info']['description'])
        pr_index(textwrap.dedent("""\

            .. toctree::
                :glob:
                :hidden:

                *
            """))

        segment = None

        uris = sorted(swagger['paths'])
        for segment, segment_uris in itertools.groupby(uris, key=segment_for_uri):

            outfile = segment.strip('/').replace('/', '_')
            with open(os.path.join(output_dir, outfile + '.rst'), 'w') as outf:
                pr_outf = functools.partial(print, file=outf)
                pr_outf(rst_header(segment, level=1, anchor="gen_" + outfile))
                pr_outf(".. openapi:: {}".format(rel_swagger_path))
                pr_outf("    :format: markdown")
                pr_outf("    :include:")
                pr_outf("        {}.*".format(segment))

            pr_index(rst_header(segment, level=2))

            for uri in segment_uris:
                methods = swagger['paths'][uri]
                for method, op_data in method_ordered_items(methods):
                    summary = ''
                    if 'summary' in op_data:
                        summary = " --- {}".format(op_data['summary'])
                    pr_index(":ref:`{} {}<gen_{}>`{}\n".format(method.upper(), uri, outfile, summary))


def main(args):
    convert_swagger_to_sphinx(swagger_file=args[0], output_dir=args[1])


if __name__ == '__main__':
    main(sys.argv[1:])
