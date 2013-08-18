"""
Provide a means to aggregate and store MongoDB related performance in our product
"""
import threading
import time
import logging
from xmodule.contentstore.content import XASSET_LOCATION_TAG
from django.conf import settings

_mongo_perf_tracker_threadlocal = threading.local()
_mongo_perf_tracker_threadlocal.data = {}

# counter to keep track of how many requests we've processed. This is used to
# keer track of when we need to flush out internal buffers out to some persistence
# layer
last_dump_time = time.time()

# global object which retains a mapping of URL to DB performance information
db_stats_per_url = {}

log = logging.getLogger("common.mongo_perf_tracker")

_perf_tracker = None

class MongoPerfTracker(object):
    """
    Implements Django middleware object which manages the lifetime of
    the performance tracker for our MongoDB store provider
    """
    @property
    def perf_tracker_data(self):
        """
        Returns the dictionary that is in the threadlocal
        """
        return _mongo_perf_tracker_threadlocal.data

    def set_perf_tracker_data_entry(self, key, value):
        """
        Sets a piece of tracking data
        """
        _mongo_perf_tracker_threadlocal.data[key] = value

    def increment_perf_tracker_counter(self, key):
        """
        Increases a counter by one
        """
        self.add_to_float_perf_tracker_counter(key, 1.0)

    def add_to_float_perf_tracker_counter(self, key, increment_float):
        """
        Adds a number to a tracking element which is a float
        """
        counter = self.perf_tracker_data[key] if key in self.perf_tracker_data else 0.0
        counter = counter + increment_float

        self.set_perf_tracker_data_entry(key, counter)

    def _is_trackable_path(self, request):
        """
        Returns whether this path is something we want to set up stats gathering for
        """
        # don't track requests for GridFS hosted assets
        if request.path.startswith('/' + XASSET_LOCATION_TAG + '/'):
            return False

        # don't track requests for things in /static/...
        if request.path.startswith('/static/'):
            return False

        # don't track POST-backs, for now at least
        if request.method in ('POST', 'PUT'):
            return False

        return True

    def clear_perf_tracker_data(self):
        """
        Resets all data in our threadlocal
        """
        _mongo_perf_tracker_threadlocal.data = {}

    def process_request(self, request):
        """
        Middleware entry point that is called on every received thread
        """
        self.clear_perf_tracker_data()

        return None

    def process_response(self, request, response):
        """
        Django middleware entry point that is called on every response sent back to client
        """
        global trackable_requests_processed, db_stats_per_url, last_dump_time

        try:
            if self._is_trackable_path(request):
                # copy over any stats gathered in this request and put in the global dictionary
                # to get written out on a periodic basis

                set_entry = True

                # take what the overwrite key should be from settings, if defined
                overwrite_key = getattr(settings, 'MONGO_PERF_TRACKER_OVERWITE_KEY', None)

                # first see if we have an entry for this path, if so see if an overwrite key
                # has been specified so that we can use that value to compare to what exists
                # this can be used to implement a high-water mark
                if request.path in db_stats_per_url and overwrite_key:
                    existing_level = db_stats_per_url[request.path].get(overwrite_key, 0)
                    new_level = self.perf_tracker_data.get(overwrite_key, 0)
                    set_entry = existing_level < new_level

                if set_entry and len(self.perf_tracker_data.keys()) > 0:
                    db_stats_per_url[request.path] = self.perf_tracker_data

                # dump stats after a certain period of time, default 1 hr
                dump_time_delta = getattr(settings, 'MONGO_PERF_DUMP_AFTER_N_MINUTES', 60.0) * 60.0

                if time.time() - last_dump_time > dump_time_delta and len(db_stats_per_url.keys()) > 0:
                    # Note, we use info level so they don't get filtered out in the logs
                    log.info('mongo_db_stats dump = {0}'.format(db_stats_per_url))
                    last_dump_time = time.time()
                    db_stats_per_url = {}
        except:
            # This is just optional perf metering, so trap all unhandled exceptions and continue
            pass

        self.clear_perf_tracker_data()
        return response

    @classmethod
    def get_perf_tracker(cls):
        global _perf_tracker
        
        if not _perf_tracker:
            _perf_tracker = MongoPerfTracker()

        return _perf_tracker
