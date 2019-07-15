import coverage
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@require_POST
@csrf_exempt
def update_context(request):
    item = request.POST.get('item')
    when = request.POST.get('when')
    current = coverage.Coverage.current()
    if current is not None and item and when:
        context = "{item.nodeid}|{when}".format(item=item, when=when)
        current.switch_context(context)
