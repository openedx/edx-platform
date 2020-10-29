"""Generate Markdown documents from an OpenAPI swagger file."""

from __future__ import print_function

import contextlib
import functools
import os
import os.path
import re
import sys

import yaml


# JSON Reference helpers

class JRefable(object):
    """An object that can be indexed with JSON Pointers, and supports $ref."""
    def __init__(self, data, doc=None, ref=None):
        self.data = data
        self.doc = doc or data
        self.ref = ref or '/'
        self.name = None

    def __repr__(self):
        return repr(self.data)

    def wrap(self, data, ref):
        if isinstance(data, dict):
            if '$ref' in data:
                ref = data['$ref']
                ret = JRefableObject(self.doc)[ref]
                ret.name = ref.split('/')[-1]
                return ret
            return JRefableObject(data, self.doc, ref)
        if isinstance(data, list):
            return JRefableArray(data, self.doc, ref)
        return data


class JRefableObject(JRefable):
    """Make a dictionary into a JSON Reference-capable object."""
    def __getitem__(self, jref):
        if jref.startswith('#/'):
            parts = jref[2:]
            data = self.doc
            ref = '/'
        else:
            parts = jref
            data = self.data
            ref = self.ref
        for part in parts.split('/'):
            try:
                data = data[part]
            except KeyError:
                raise KeyError("{!r} not in {!r} then {!r}".format(part, self.ref, jref))
            ref = ref + part + '/'
        return self.wrap(data, ref=ref)

    def get(self, key, default=None):
        if key in self.data:
            return self.wrap(self.data[key], self.ref + key + '/')
        return default

    def keys(self):
        return self.data.keys()

    def items(self):
        for k, v in self.data.items():
            yield k, self.wrap(v, self.ref + k.replace('/', ':') + '/')

    def __contains__(self, val):
        return val in self.data


class JRefableArray(JRefable):
    """Make a list into a JSON Reference-capable array."""
    def __getitem__(self, index):
        try:
            data = self.data[index]
        except IndexError:
            raise IndexError("{!r} not in {!r}".format(index, self.ref))
        return self.wrap(data, self.ref + str(index) + '/')

    def __iter__(self):
        for i, elt in enumerate(self.data):
            yield self.wrap(elt, self.ref + str(i) + '/')


class OutputFiles(object):
    """A context manager to manage a series of files.

    Use like this::

        with OutputFiles() as outfiles:
            ...
            if some_condition():
                f = outfiles.open("filename.txt", "w")

    Each open will close the previously opened file, and the end of the with
    statement will close the last one.

    """
    def __init__(self):
        self.file = None

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        if self.file:
            self.file.close()
        return False

    def open(self, *args, **kwargs):
        if self.file:
            self.file.close()
        self.file = open(*args, **kwargs)
        return self.file


sluggers = [
    r"^.*?/v\d+/[\w_-]+",
    r"^(/[\w_-]+){,3}",
]

method_order = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']


def method_ordered_items(method_data):
    keys = [k for k in method_order if k in method_data]
    for key in keys:
        yield key, method_data[key]


class MarkdownWriter(object):
    """Help write markdown, managing indentation and header nesting."""

    def __init__(self, outfile):
        self.outfile = outfile
        self.cur_indent = 0

    def print(self, text='', increase_headers=0):
        if increase_headers:
            text = re.sub(r"^#", "#" * (increase_headers + 1), text, flags=re.MULTILINE)
        if self.cur_indent:
            text = re.sub(r"^", " " * self.cur_indent, text, flags=re.MULTILINE)
        print(text, file=self.outfile)

    @contextlib.contextmanager
    def indent(self, spaces):
        old_indent = self.cur_indent
        self.cur_indent += spaces
        try:
            yield
        finally:
            self.cur_indent = old_indent


def convert_swagger_to_markdown(swagger_data, output_dir):
    """Convert a swagger.yaml file to a series of markdown documents."""
    sw = JRefableObject(swagger_data)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(os.path.join(output_dir, 'index.md'), 'w') as index:
        indexmd = MarkdownWriter(index)
        indexmd.print("# {}\n".format(sw['info/title']))
        indexmd.print(sw['info/description'])
        indexmd.print()

        with OutputFiles() as outfiles:
            slug = None

            for uri, methods in sorted(sw['paths'].items()):
                for slugger in sluggers:
                    m = re.search(slugger, uri)
                    if m:
                        new_slug = m.group()
                        if new_slug != slug:
                            slug = new_slug
                            outfile = slug.strip('/').replace('/', '_') + '.md'
                            outf = outfiles.open(os.path.join(output_dir, outfile), 'w')
                            outmd = MarkdownWriter(outf)
                            outmd.print("# {}\n".format(slug))
                            indexmd.print("## {}\n".format(slug))
                        break

                common_params = methods.get('parameters', [])
                for method, op_data in method_ordered_items(methods):
                    summary = ''
                    if 'summary' in op_data:
                        summary = " --- {}".format(op_data['summary'])
                    indexmd.print("[{} {}]({}){}\n".format(method.upper(), uri, outfile, summary))
                    write_one_method(outmd, method, uri, op_data, common_params)


def write_one_method(outmd, method, uri, op_data, common_params):
    """Write one entry (uri and method) to the markdown output."""
    outmd.print("\n## {} {}\n".format(method.upper(), uri))
    if 'summary' in op_data:
        outmd.print(op_data['summary'])
        outmd.print()
    outmd.print(op_data['description'], increase_headers=2)

    params = list(op_data.get('parameters', []))
    params.extend(common_params)
    if params:
        outmd.print("\n### Parameters\n")
        for param in params:
            description = param.get('description', '').strip()
            if description:
                description = ": " + description
            where = param['in']
            required = param.get('required', False)
            required = "required" if required else "optional"
            if where == 'body':
                schema = param['schema']
                outmd.print("- **{}** (body, {}){}".format(
                    param['name'],
                    schema.name or schema['type'],
                    description,
                ))
                with outmd.indent(2):
                    write_schema(outmd, schema)
            else:
                outmd.print("- **{}** ({}, {}, {}){}".format(
                    param['name'],
                    where,
                    param['type'],
                    required,
                    description,
                ))

    responses = op_data.get('responses', [])
    if responses:
        outmd.print("\n### Responses\n")
        for status, response in sorted(responses.items()):
            description = response.get('description', '').strip()
            if description:
                description = ": " + description
            schema = response.get('schema')
            if schema:
                type_note = " ({})".format(type_name(schema))
            else:
                type_note = ""
            outmd.print("- **{}**{}{}".format(
                status,
                type_note,
                description,
            ))
            if schema:
                with outmd.indent(2):
                    write_schema(outmd, schema)


def type_name(schema):
    """What is the short type name for `schema`?"""
    if schema['type'] == 'object':
        return schema.name or schema.get('type') or "object"
    elif schema['type'] == 'array':
        item_type = type_name(schema['items'])
        return "array of " + item_type
    else:
        return schema['type']


def write_schema(outmd, schema):
    """Write a schema to the markdown output."""
    if schema['type'] == 'object':
        required = set(schema.get('required', ()))
        for prop_name, prop in sorted(schema['properties'].items()):
            attrs = []
            type = type_name(prop)
            if prop['type'] == 'array':
                item_type = prop['items']
            else:
                item_type = None
            attrs.append(type)
            if prop_name in required:
                attrs.append("required")
            else:
                attrs.append("optional")
            if 'format' in prop:
                attrs.append("format {}".format(prop["format"]))
            if 'pattern' in prop:
                attrs.append("pattern `{}`".format(prop["pattern"]))
            if 'minLength' in prop:
                attrs.append("min length {}".format(prop["minLength"]))
            if 'maxLength' in prop:
                attrs.append("max length {}".format(prop["maxLength"]))
            if 'minimum' in prop:
                attrs.append("minimum {}".format(prop["minimum"]))
            if 'maximum' in prop:
                attrs.append("maximum {}".format(prop["maximum"]))
            if prop.get('readOnly', False):
                attrs.append("read only")
            # TODO: enum
            # TODO: x-nullable

            title = prop.get('title', '').strip()
            if title:
                title = ": " + title
            description = prop.get('description', '').strip()
            if description:
                if title:
                    title = title + ". " + description
                else:
                    title = ": " + description

            outmd.print("- **{name}** ({attrs}){title}".format(
                name=prop_name,
                attrs=", ".join(attrs),
                title=title,
            ))
            if item_type and item_type['type'] in ['object', 'array']:
                with outmd.indent(2):
                    write_schema(outmd, item_type)
    elif schema['type'] == 'array':
        write_schema(outmd, schema['items'])
    else:
        raise ValueError("Don't understand schema type {!r} at {}".format(schema['type'], schema.ref))


def main(args):
    with open(args[0]) as swyaml:
        swagger_data = yaml.safe_load(swyaml)
    convert_swagger_to_markdown(swagger_data, output_dir=args[1])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
