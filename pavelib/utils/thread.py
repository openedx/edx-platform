"""
Helper functions for managing threads.
"""
import multiprocessing


def _get_func_args(func):
    args = []
    kwargs = {}
    if not hasattr(func, '__iter__'):
        return func, args, kwargs
    f = func[0]
    if len(func) > 1:
        args = func[1]
        if len(func) > 2:
            kwargs = func[2]
    return f, args, kwargs


def run_threaded(funcs_to_run):
    """
    Run a list of functions in parallel, returning when all have completed.
    expects a list of (function, args, kwargs)
    """
    try:
        from concurrent.futures import ThreadPoolExecutor
    except ImportError:
        from threading import Thread
        threads = []
        for func in funcs_to_run:
            f, args, kwargs = _get_func_args(func)
            t = Thread(target=f, args=args, kwargs=kwargs)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
    else:
        with ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
            for func in funcs_to_run:
                f, args, kwargs = _get_func_args(func)
                executor.submit(f, *args, **kwargs)
