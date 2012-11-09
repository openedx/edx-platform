import xmodule
from xmodule import progress


def SequenceModule(XModule, ResourceTemplateModule):

    def __init__(self, definition, policy, state, preferences):
        self.state = state

    @property
    def visited(self):
        return set(self.state['visited'])

    @property
    def possible(self):
        return set(child.id for child in self.children)

    @xmodule.register_view('student')
    @xmodule.register_view('instructor')
    def student_view(self):
        return self.render_template(
            'main',
            # Render w/ no arguments executes the same view for the children
            # that is currently rendering for the parent
            children=[child.render() for child in self.children]
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


def ChemistryEquationModule(XModule, ResourceTemplateModule):

    def __init__(self, definition, policy, state, preferences):
        self.state = state

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