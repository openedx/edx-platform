
"""
Namespace defining common fields used by Studio for all blocks
"""

import datetime
import textwrap

from xblock.fields import Scope, Field, Integer, XBlockMixin
from xblock.fragment import Fragment


class DateTuple(Field):
    """
    Field that stores datetime objects as time tuples
    """
    def from_json(self, value):
        return datetime.datetime(*value[0:6])

    def to_json(self, value):
        if value is None:
            return None

        return list(value.timetuple())


class CmsBlockMixin(XBlockMixin):
    """
    Mixin with fields common to all blocks in Studio
    """
    published_date = DateTuple(help="Date when the module was published", scope=Scope.settings)
    published_by = Integer(help="Id of the user who published this module", scope=Scope.settings)

    def studio_view(self, context):
        """
        A default studio view that has instructions on modifying the content directly
        in mongodb (temporary for the datajam)
        """
        update_string = textwrap.dedent("""
            db.modulestore.update(
                {{
                    _id.org: '{location.org}',
                    _id.course: '{location.course}',
                    _id.category: '{location.category}',
                    _id.name: '{location.name}',
                }},
                {{ $set: {{ {field_name}: '&lt;insert your value here&gt;' }}}},
                {{ multi: true }}
            )
        """)

        commands = {}

        for field in getattr(self, 'unmixed_class', self).fields.values():
            if field.scope == Scope.content:
                commands[field.name] = update_string.format(location=self.location, field_name='definition.' + field.name)
            elif field.scope == Scope.settings:
                commands[field.name] = update_string.format(location=self.location, field_name='metadata.' + field.name)
            elif field.scope == Scope.children:
                commands[field.name] = update_string.format(location=self.location, field_name='definition.children')
            else:
                continue

        table_row = "<tr><td>{}</td><td><pre>{}</pre></td></tr>"

        return Fragment(textwrap.dedent(u"""
            <div>
            Update the fields in this XBlock by using the following commands in the mongodb cli
            <table>
            <tr><th>Field Name</th><th>Command</th></tr>
            {}
            </table>
        """).format('\n'.join(table_row.format(name, command) for name, command in commands.iteritems())))
