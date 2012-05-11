from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response

@login_required
def index(request, page=0): 
    return render_to_response('staticbook.html',{'page':int(page)})

def index_shifted(request, page):
    return index(request, int(page)+24)
