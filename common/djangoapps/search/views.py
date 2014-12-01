from django.utils.translation import ugettext as _

from manager import SearchEngine
from django.http import HttpResponse
import json


def do_search(request, course_id=None):
    results = {
        "error": _("Nothing to search")
    }
    status_code = 500

    try:
        if request.method == 'POST':
            field_dictionary = None
            if course_id:
                field_dictionary = {"course_id": course_id}
            searcher = SearchEngine.get_search_engine("courseware_index")
            results = searcher.search_string(
                request.POST["search_string"], field_dictionary=field_dictionary)
            status_code = 200
    except Exception as err:
        results = {
            "error": str(err)
        }

    return HttpResponse(
        json.dumps(results),
        content_type='application/json',
        status=status_code
    )
