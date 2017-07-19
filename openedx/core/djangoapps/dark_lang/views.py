"""
Views file for the Darklang Django App
"""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic.base import View
from edxmako.shortcuts import render_to_response
from openedx.core.lib.api.view_utils import view_auth_classes


@view_auth_classes()
class DarkLangView(View):
    """
    View used when a user is attempting to change the preview language using Darklang.

    Expected Behavior:
    GET - returns a form for setting/resetting the user's dark language
    POST - updates or clears the setting to the given dark language
    """
    template_name = 'darklang/preview_lang.html'

    @method_decorator(login_required)
    def get(self, request):
        """
        Returns the Form for setting/resetting a User's dark language setting

        Arguments:
            request (Request): The Django Request Object

        Returns:
            HttpResponse: View containing the form for setting the preview lang
        """
        context = {
            'disable_courseware_js': True,
            'uses_bootstrap': True,
        }
        return render_to_response(self.template_name, context)

    @method_decorator(login_required)
    def post(self, request):
        """
        Sets or clears the DarkLang depending on the incoming post data.

        Arguments:
            request (Request): The Django Request Object

        Returns:
            HttpResponse: View containing the form for setting the preview lang with the status
                included in the context
        """
        return self.get(request)
