"""Organizations views for use with Studio."""
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.http import HttpResponse

from openedx.core.lib.js_utils import escape_json_dumps
from util.organizations_helpers import get_organizations


class OrganizationListView(View):
    """View rendering organization list as json.

    This view renders organization list json which is used in org
    autocomplete while creating new course.
    """

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        """Returns organization list as json."""
        organizations = get_organizations()
        org_names_list = [(org["short_name"]) for org in organizations]
        return HttpResponse(escape_json_dumps(org_names_list), content_type='application/json; charset=utf-8')
