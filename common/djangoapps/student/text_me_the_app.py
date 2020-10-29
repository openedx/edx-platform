"""
Fragment for rendering text me the app.
"""


from django.template.loader import render_to_string
from web_fragments.fragment import Fragment

from openedx.core.djangoapps.plugin_api.views import EdxFragmentView


class TextMeTheAppFragmentView(EdxFragmentView):
    """
    A fragment to text me the app.

    In future we can add this to learner dashboard.
    """
    def render_to_fragment(self, request, **kwargs):
        """
        Render text me the app fragment.
        """
        html = render_to_string('learner_dashboard/text-me-fragment.html', {})
        return Fragment(html)
