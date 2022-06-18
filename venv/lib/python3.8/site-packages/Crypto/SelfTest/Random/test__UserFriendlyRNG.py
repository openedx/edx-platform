# -*- coding: utf-8 -*-
# Self-tests for the user-friendly Crypto.Random interface
#
# Written in 2013 by Dwayne C. Litzenberger <dlitz@dlitz.net>
#
# ===================================================================
# The contents of this file are dedicated to the public domain.  To
# the extent that dedication to the public domain is not available,
# everyone is granted a worldwide, perpetual, royalty-free,
# non-exclusive license to exercise all rights associated with the
# contents of this file for any purpose whatsoever.
# No rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================

"""Self-test suite for generic Crypto.Random stuff """



__revision__ = "$Id$"

import binascii
import pprint
import unittest
import os
import time
import sys
if sys.version_info[0] == 2 and sys.version_info[1] == 1:
    from Crypto.Util.py21compat import *
from Crypto.Util.py3compat import *

try:
    import multiprocessing
except ImportError:
    multiprocessing = None

import Crypto.Random._UserFriendlyRNG
import Crypto.Random.random

class RNGForkTest(unittest.TestCase):

    def _get_reseed_count(self):
        """
        Get `FortunaAccumulator.reseed_count`, the global count of the
        number of times that the PRNG has been reseeded.
        """
        rng_singleton = Crypto.Random._UserFriendlyRNG._get_singleton()
        rng_singleton._lock.acquire()
        try:
            return rng_singleton._fa.reseed_count
        finally:
            rng_singleton._lock.release()

    def runTest(self):
        # Regression test for CVE-2013-1445.  We had a bug where, under the
        # right conditions, two processes might see the same random sequence.

        if sys.platform.startswith('win'):  # windows can't fork
            assert not hasattr(os, 'fork')    # ... right?
            return

        # Wait 150 ms so that we don't trigger the rate-limit prematurely.
        time.sleep(0.15)

        reseed_count_before = self._get_reseed_count()

        # One or both of these calls together should trigger a reseed right here.
        Crypto.Random._UserFriendlyRNG._get_singleton().reinit()
        Crypto.Random.get_random_bytes(1)

        reseed_count_after = self._get_reseed_count()
        self.assertNotEqual(reseed_count_before, reseed_count_after)  # sanity check: test should reseed parent before forking

        rfiles = []
        for i in range(10):
            rfd, wfd = os.pipe()
            if os.fork() == 0:
                # child
                os.close(rfd)
                f = os.fdopen(wfd, "wb")

                Crypto.Random.atfork()

                data = Crypto.Random.get_random_bytes(16)

                f.write(data)
                f.close()
                os._exit(0)
            # parent
            os.close(wfd)
            rfiles.append(os.fdopen(rfd, "rb"))

        results = []
        results_dict = {}
        for f in rfiles:
            data = binascii.hexlify(f.read())
            results.append(data)
            results_dict[data] = 1
            f.close()

        if len(results) != len(list(results_dict.keys())):
            raise AssertionError("RNG output duplicated across fork():\n%s" %
                                 (pprint.pformat(results)))


# For RNGMultiprocessingForkTest
def _task_main(q):
    a = Crypto.Random.get_random_bytes(16)
    time.sleep(0.1)     # wait 100 ms
    b = Crypto.Random.get_random_bytes(16)
    q.put(binascii.b2a_hex(a))
    q.put(binascii.b2a_hex(b))
    q.put(None)      # Wait for acknowledgment


class RNGMultiprocessingForkTest(unittest.TestCase):

    def runTest(self):
        # Another regression test for CVE-2013-1445.  This is basically the
        # same as RNGForkTest, but less compatible with old versions of Python,
        # and a little easier to read.

        n_procs = 5
        manager = multiprocessing.Manager()
        queues = [manager.Queue(1) for i in range(n_procs)]

        # Reseed the pool
        time.sleep(0.15)
        Crypto.Random._UserFriendlyRNG._get_singleton().reinit()
        Crypto.Random.get_random_bytes(1)

        # Start the child processes
        pool = multiprocessing.Pool(processes=n_procs, initializer=Crypto.Random.atfork)
        map_result = pool.map_async(_task_main, queues)

        # Get the results, ensuring that no pool processes are reused.
        aa = [queues[i].get(30) for i in range(n_procs)]
        bb = [queues[i].get(30) for i in range(n_procs)]
        res = list(zip(aa, bb))

        # Shut down the pool
        map_result.get(30)
        pool.close()
        pool.join()

        # Check that the results are unique
        if len(set(aa)) != len(aa) or len(set(res)) != len(res):
            raise AssertionError("RNG output duplicated across fork():\n%s" %
                                 (pprint.pformat(res),))


def get_tests(config={}):
    tests = []
    tests += [RNGForkTest()]
    if multiprocessing is not None:
        tests += [RNGMultiprocessingForkTest()]
    return tests

if __name__ == '__main__':
    suite = lambda: unittest.TestSuite(get_tests())
    unittest.main(defaultTest='suite')

# vim:set ts=4 sw=4 sts=4 expandtab:
