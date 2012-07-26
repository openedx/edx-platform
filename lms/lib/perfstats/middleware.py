import json
import tempfile
import time

from django.conf import settings
from django.db import connection

import views


class ProfileMiddleware:
    def process_request(self, request):
        self.t = time.time()
        print "Process request"

    def process_response(self, request, response):
        # totalTime = time.time() - self.t
        # tmpfile = tempfile.NamedTemporaryFile(prefix='sqlprof-t=' + str(totalTime) + "-", delete=False)

        # output = ""
        # for query in connection.queries:
        #     output += "Time: " + str(query['time']) + "\nQuery: " + query['sql'] + "\n\n"

        # tmpfile.write(output)

        # print "SQL Log file: " , tmpfile.name
        # tmpfile.close()

        # print "Process response"
        return response
