import queue
import threading
from concurrent.futures import Executor, Future


class _WorkItem:
    """
    Represents an item needing to be run in the executor.
    Copied from ThreadPoolExecutor (but it's private, so we're not going to rely on importing it)
    """

    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return
        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as exc:
            self.future.set_exception(exc)
            # Break a reference cycle with the exception 'exc'
            self = None
        else:
            self.future.set_result(result)


class CurrentThreadExecutor(Executor):
    """
    An Executor that actually runs code in the thread it is instantiated in.
    Passed to other threads running async code, so they can run sync code in
    the thread they came from.
    """

    def __init__(self):
        self._work_thread = threading.current_thread()
        self._work_queue = queue.Queue()
        self._broken = False

    def run_until_future(self, future):
        """
        Runs the code in the work queue until a result is available from the future.
        Should be run from the thread the executor is initialised in.
        """
        # Check we're in the right thread
        if threading.current_thread() != self._work_thread:
            raise RuntimeError(
                "You cannot run CurrentThreadExecutor from a different thread"
            )
        future.add_done_callback(self._work_queue.put)
        # Keep getting and running work items until we get the future we're waiting for
        # back via the future's done callback.
        try:
            while True:
                # Get a work item and run it
                work_item = self._work_queue.get()
                if work_item is future:
                    return
                work_item.run()
                del work_item
        finally:
            self._broken = True

    def submit(self, fn, *args, **kwargs):
        # Check they're not submitting from the same thread
        if threading.current_thread() == self._work_thread:
            raise RuntimeError(
                "You cannot submit onto CurrentThreadExecutor from its own thread"
            )
        # Check they're not too late or the executor errored
        if self._broken:
            raise RuntimeError("CurrentThreadExecutor already quit or is broken")
        # Add to work queue
        f = Future()
        work_item = _WorkItem(f, fn, args, kwargs)
        self._work_queue.put(work_item)
        # Return the future
        return f
