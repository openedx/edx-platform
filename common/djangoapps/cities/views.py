from django.utils import simplejson
from django.http import HttpResponse
from models import City

def lookup_handler(request):
    """
    TODO: doc
    """
    results = ['No encontrado']
    if request.is_ajax() and request.method == 'GET':
        if request.GET.get('query', False):
            query = request.GET.get('query')
            model_results = City.objects.filter(name__icontains=query)
            results = [[str(x.id),str(x)] for x in model_results]
    json_data = simplejson.dumps(results)
    return HttpResponse(json_data, mimetype='application/json')
