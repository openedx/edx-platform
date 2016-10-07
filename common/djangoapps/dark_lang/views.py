"""
Views file for the Darklang Django App
"""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.translation import LANGUAGE_SESSION_KEY
from django.utils.translation import ugettext as _
from django.views.generic.base import View
from openedx.core.djangoapps.user_api.preferences.api import (
    delete_user_preference, get_user_preference, set_user_preference
)
from openedx.core.lib.api.view_utils import view_auth_classes

from dark_lang import DARK_LANGUAGE_KEY
from dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.edxmako.shortcuts import render_to_response
from lang_pref import LANGUAGE_KEY

LANGUAGE_INPUT_FIELD = 'preview_lang'


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
            'uses_pattern_library': True
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
        return self.process_darklang_request(request)

    def process_darklang_request(self, request):
        """
        Proccess the request to Set or clear the DarkLang depending on the incoming request.

        Arguments:
            request (Request): The Django Request Object

        Returns:
            HttpResponse: View containing the form for setting the preview lang with the status
                included in the context
        """
        context = {
            'disable_courseware_js': True,
            'uses_pattern_library': True
        }
        response = None
        if not DarkLangConfig.current().enabled:
            message = _('Preview Language is currently disabled')
            context.update({'form_submit_message': message})
            context.update({'success': False})
            response = render_to_response(self.template_name, context, request=request)

        elif 'set_language' in request.POST:
            # Set the Preview Language
            response = self._set_preview_language(request, context)
        elif 'reset' in request.POST:
            # Reset and clear the language preference
            response = self._clear_preview_language(request, context)
        return response

    def _set_preview_language(self, request, context):
        """
        Set the Preview language

        Arguments:
            request (Request): The incoming Django Request
            context dict: The basic context for the Response

        Returns:
            HttpResponse: View containing the form for setting the preview lang with the status
                included in the context
        """
        message = None
        show_refresh_message = False

        preview_lang = request.POST.get(LANGUAGE_INPUT_FIELD, '')
        if not preview_lang.strip():
            message = _('Language code not provided')
        else:
            # Set the session key to the requested preview lang
            request.session[LANGUAGE_SESSION_KEY] = preview_lang

            # Make sure that we set the requested preview lang as the dark lang preference for the
            # user, so that the lang_pref middleware doesn't clobber away the dark lang preview.
            auth_user = request.user
            if auth_user:
                set_user_preference(request.user, DARK_LANGUAGE_KEY, preview_lang)

            message = _('Language set to language code: {preview_language_code}').format(
                preview_language_code=preview_lang
            )
            show_refresh_message = True
        context.update({'form_submit_message': message})
        context.update({'success': show_refresh_message})
        response = render_to_response(self.template_name, context)
        return response

    def _clear_preview_language(self, request, context):
        """
        Clears the dark language preview

        Arguments:
            request (Request): The incoming Django Request
            context dict: The basic context for the Response
        Returns:
            HttpResponse: View containing the form for setting the preview lang with the status
                included in the context
        """
        # delete the session language key (if one is set)
        if LANGUAGE_SESSION_KEY in request.session:
            del request.session[LANGUAGE_SESSION_KEY]

        user_pref = ''
        auth_user = request.user
        if auth_user:
            # Reset user's dark lang preference to null
            delete_user_preference(auth_user, DARK_LANGUAGE_KEY)
            # Get & set user's preferred language
            user_pref = get_user_preference(auth_user, LANGUAGE_KEY)
            if user_pref:
                request.session[LANGUAGE_SESSION_KEY] = user_pref
        if user_pref is None:
            message = _('Language reset to the default language code')
        else:
            message = _("Language reset to user's preference: {preview_language_code}").format(
                preview_language_code=user_pref
            )
        context.update({'form_submit_message': message})
        context.update({'success': True})
        return render_to_response(self.template_name, context)
