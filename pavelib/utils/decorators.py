""" a collection of utililty decorators for paver tasks """

import multiprocessing
from Queue import Empty
from functools import wraps

import psutil


def timeout(limit=60):
    """
    kill a function if it has not completed within a specified timeframe
    """

    def _handle_function_process(*args, **kwargs):
        """ helper function for running a function and getting its output """
        queue = kwargs['queue']
        function = kwargs['function_to_call']
        function_args = args
        function_kwargs = kwargs['function_kwargs']
        function_output = function(*function_args, **function_kwargs)
        queue.put(function_output)

    def decorated_function(function):
        """ the time-limited function returned by the timeout decorator """

        def function_wrapper(*args, **kwargs):
            """
            take a function and run it on a separate process, forcing it to
            either give up its return value or throw a TimeoutException with
            a specified timeframe (in seconds)
            """
            queue = multiprocessing.Queue()
            args_tuple = tuple(a for a in args)
            meta_kwargs = {
                'function_to_call': function, 'queue': queue,
                'function_kwargs': kwargs
            }
            function_proc = multiprocessing.Process(
                target=_handle_function_process, args=args_tuple, kwargs=meta_kwargs
            )
            function_proc.start()
            function_proc.join(float(limit))
            # If the process is still alive after attempting to join after
            # the time limit, it is considered it to have 'timed out'
            timed_out = function_proc.is_alive()
            try:
                function_output = queue.get()
            except Empty:
                # 'get' raises an Empty exception if the queue has no value,
                # however, since this decorator can be applied to functions
                # with no return value, this exception is not useful and
                # should be escaped
                function_output = None

            # Clean up any remnants of lingering processes, without calling
            # Process.terminate(), as this seems to cause problems with
            # pytest x-dist
            queue.close()
            function_proc.join()
            queue.join_thread()
            if timed_out:
                raise TimeoutException
            return function_output

        return wraps(function)(function_wrapper)

    return decorated_function


class TimeoutException(Exception):
    pass
