from datetime import datetime
from cProfile import Profile
from pstats import Stats

class ProfilingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        prof = None
        if request.GET.get('profile_name'):
            prof = Profile()
            prof.enable()

        response = self.get_response(request)

        if prof:
            prof.disable()
            s = Stats(prof)
            s.dump_stats(request.GET['profile_name'])
            prof = None

        return response
