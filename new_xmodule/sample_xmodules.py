import xmodule
from xmodule import progress

class StudentDefinition(ResourceTemplate):

    definition = BaseDefinition

    def __init__(self, definition, state, preferences):
        self.definition = definition
        self.state = state
        self.preferences = preferences

    @lazy_property
    def children(self):
        return [definition.get_student_definition() for definition in self.definition.children]

    def render(self, child, context=None):
        if context is None:
            context = self.render_context

        # Make children use the appropriate render context
        child.render_context = context
        return child.find_view(context)()

    def find_view(self, context):
        # self._views is populated with metaclass magic that is TBD
        return self._views[context]


class BaseDefinition(ResourceTemplate):
    def __init__(self, content, policy, child_pointers):
        self.content = content
        self.policy = policy
        self.child_pointers = child_pointers

    @lazy_property
    def children(self):
        return [xmodule.get_definition(child_ptr) for child_ptr in self.definition.child_pointers]

    @xmodule.register_view('edit')
    def edit(self):
        return self.render_template(
            'combined',
            content=self.render(self, 'edit_content'),
            policy=self.render(self, 'edit_policy'),
            children=self.render(self, 'edit_children'),
        )

    @xmodule.register_view('edit_children')
    def edit_children(self):
        return self.render_template(
            'drag_and_drop',
            children=self.children
        )

    @xmodule.register_view('edit_policy')
    def edit_policy(self):
        return self.render_template(
            'mapping',
            mapping=self.policy
        )

    @xmodule.register_view('edit_content')
    def edit_content(self):
        return self.render_template(
            'mapping',
            mapping=self.content
        )

    @xmodule.register_handler('update_children')
    def update_children(self, data):
        """
        Expects a new list of child xmodule ids
        """
        self.children = data['children']

    @xmodule.register_handler('set_policy')
    def set_policy(self, data):
        """
        Expects keys 'name' and 'value'.
        If value is None, then delete the key, otherwise set
        the named key to the value
        """
        if data['value'] is None:
            del self.policy[data['value']]
        else:
            self.policy[data['name']] = self.policy[data['value']]

class SequenceDefinition(BaseDefinition):

    @xmodule.register_view('edit')
    def edit(self):
        return self.render_template(
            'combined',
            children=self.render(self, 'edit_children'),
            policy=self.render(self, 'edit_policy'),
        )

    @xmodule.register_view('edit_content')
    def empty_view(self):
        return None

class SequenceStudentDefinition(StudentDefinition):

    definition = SequenceDefinition

    @property
    def visited(self):
        """
        Return the set of ids that this user has visited in the past
        """
        return set(self.state['visited'])

    @property
    def possible(self):
        """
        Return the set of ids in this sequence that a student could have visited
        """
        return set(child.id for child in self.children)

    @xmodule.register_view('student')
    @xmodule.register_view('instructor')
    def student_view(self):
        return self.render_template(
            'main',
            # Render w/ no arguments executes the same view for the children
            # that is currently rendering for the parent
            children=[self.render(child) for child in self.children]
        )

    @xmodule.register_handler('update_position')
    def update_position(self, data):
        new_position = self.children[data['position']].id
        # Updates to the state dictionary are transparently saved to the db
        self.state['position'] = new_position
        self.state['visited'] = self.visited.union(new_position)
        self.update_progress()

    def update_progress(self):
        progress.publish({
            'visited': (len(self.visited & self.possible), len(self.possible))
        })


class ChemistryEquationStudentDefinition(StudentDefinition):

    @xmodule.register_view('student')
    def student_view(self):
        return self.render_template(
            'main',
            equation=self.state['equation'],
            rendered_equation=self.render_equation(self.state['equation'])
        )

    @xmodule.register_handler('render_eq')
    def render_eq_handler(self, data):
        self.state['equation'] = data['equation']
        return self.render_equation(data['equation'])

    def render_equation(self, equation):
        return PIL.render_render_render(equation)