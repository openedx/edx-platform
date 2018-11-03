"""Module containing a preprocessor that executes the code cells
and updates outputs"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

from textwrap import dedent
from contextlib import contextmanager

try:
    from queue import Empty  # Py 3
except ImportError:
    from Queue import Empty  # Py 2

from traitlets import List, Unicode, Bool, Enum, Any, Type, Dict, Integer, default

from nbformat.v4 import output_from_msg

from .base import Preprocessor
from ..utils.exceptions import ConversionException


class CellExecutionError(ConversionException):
    """
    Custom exception to propagate exceptions that are raised during
    notebook execution to the caller. This is mostly useful when
    using nbconvert as a library, since it allows to deal with
    failures gracefully.
    """
    def __init__(self, traceback):
        super(CellExecutionError, self).__init__(traceback)
        self.traceback = traceback

    def __str__(self):
        s = self.__unicode__()
        if not isinstance(s, str):
            s = s.encode('utf8', 'replace')
        return s

    def __unicode__(self):
        return self.traceback

    @classmethod
    def from_cell_and_msg(cls, cell, msg):
        """Instantiate from a code cell object and a message contents
        (message is either execute_reply or error)
        """
        tb = '\n'.join(msg.get('traceback', []))
        return cls(exec_err_msg.format(cell=cell, traceback=tb,
                                       ename=msg.get('ename', '<Error>'),
                                       evalue=msg.get('evalue', '')
                                      ))

exec_err_msg = u"""\
An error occurred while executing the following cell:
------------------
{cell.source}
------------------

{traceback}
{ename}: {evalue}
"""

class ExecutePreprocessor(Preprocessor):
    """
    Executes all the cells in a notebook
    """

    timeout = Integer(30, allow_none=True,
        help=dedent(
            """
            The time to wait (in seconds) for output from executions.
            If a cell execution takes longer, an exception (TimeoutError
            on python 3+, RuntimeError on python 2) is raised.

            `None` or `-1` will disable the timeout. If `timeout_func` is set,
            it overrides `timeout`.
            """
        )
    ).tag(config=True)

    timeout_func = Any(
        default_value=None,
        allow_none=True,
        help=dedent(
            """
            A callable which, when given the cell source as input,
            returns the time to wait (in seconds) for output from cell
            executions. If a cell execution takes longer, an exception
            (TimeoutError on python 3+, RuntimeError on python 2) is
            raised.

            Returning `None` or `-1` will disable the timeout for the cell.
            Not setting `timeout_func` will cause the preprocessor to
            default to using the `timeout` trait for all cells. The
            `timeout_func` trait overrides `timeout` if it is not `None`.
            """
        )
    ).tag(config=True)

    interrupt_on_timeout = Bool(False,
        help=dedent(
            """
            If execution of a cell times out, interrupt the kernel and
            continue executing other cells rather than throwing an error and
            stopping.
            """
        )
    ).tag(config=True)

    startup_timeout = Integer(60,
        help=dedent(
            """
            The time to wait (in seconds) for the kernel to start.
            If kernel startup takes longer, a RuntimeError is
            raised.
            """
        )
    ).tag(config=True)

    allow_errors = Bool(False,
        help=dedent(
            """
            If `False` (default), when a cell raises an error the
            execution is stopped and a `CellExecutionError`
            is raised.
            If `True`, execution errors are ignored and the execution
            is continued until the end of the notebook. Output from
            exceptions is included in the cell output in both cases.
            """
        )
    ).tag(config=True)

    force_raise_errors = Bool(False,
        help=dedent(
            """
            If False (default), errors from executing the notebook can be
            allowed with a `raises-exception` tag on a single cell, or the
            `allow_errors` configurable option for all cells. An allowed error
            will be recorded in notebook output, and execution will continue.
            If an error occurs when it is not explicitly allowed, a
            `CellExecutionError` will be raised.
            If True, `CellExecutionError` will be raised for any error that occurs
            while executing the notebook. This overrides both the
            `allow_errors` option and the `raises-exception` cell tag.
            """
        )
    ).tag(config=True)

    extra_arguments = List(Unicode())

    kernel_name = Unicode('',
        help=dedent(
            """
            Name of kernel to use to execute the cells.
            If not set, use the kernel_spec embedded in the notebook.
            """
        )
    ).tag(config=True)

    @default('kernel_name')
    def _kernel_name_default(self):
        try:
            return self.nb.metadata.get('kernelspec', {}).get('name', 'python')
        except AttributeError:
            raise AttributeError('You did not specify a kernel_name for '
                                 'the ExecutePreprocessor and you have not set '
                                 'self.nb to be able to use that to infer the '
                                 'kernel_name.')

    raise_on_iopub_timeout = Bool(False,
        help=dedent(
            """
            If `False` (default), then the kernel will continue waiting for
            iopub messages until it receives a kernel idle message, or until a
            timeout occurs, at which point the currently executing cell will be
            skipped. If `True`, then an error will be raised after the first
            timeout. This option generally does not need to be used, but may be
            useful in contexts where there is the possibility of executing
            notebooks with memory-consuming infinite loops.
            """
            )
    ).tag(config=True)

    iopub_timeout = Integer(4, allow_none=False,
        help=dedent(
            """
            The time to wait (in seconds) for IOPub output. This generally
            doesn't need to be set, but on some slow networks (such as CI
            systems) the default timeout might not be long enough to get all
            messages.
            """
        )
    ).tag(config=True)

    shutdown_kernel = Enum(['graceful', 'immediate'],
        default_value='graceful',
        help=dedent(
            """
            If `graceful` (default), then the kernel is given time to clean
            up after executing all cells, e.g., to execute its `atexit` hooks.
            If `immediate`, then the kernel is signaled to immediately
            terminate.
            """
            )
    ).tag(config=True)

    kernel_manager_class = Type(
        config=True,
        help='The kernel manager class to use.'
    )
    @default('kernel_manager_class')
    def _kernel_manager_class_default(self):
        """Use a dynamic default to avoid importing jupyter_client at startup"""
        try:
            from jupyter_client import KernelManager
        except ImportError:
            raise ImportError("`nbconvert --execute` requires the jupyter_client package: `pip install jupyter_client`")
        return KernelManager

    _display_id_map = Dict(
        help=dedent(
              """
              mapping of locations of outputs with a given display_id
              tracks cell index and output index within cell.outputs for
              each appearance of the display_id
              {
                   'display_id': {
                  cell_idx: [output_idx,]
                   }
              }
              """))

    def start_new_kernel(self, **kwargs):
        """Creates a new kernel manager and kernel client.

        Parameters
        ----------
        kwargs :
            Any options for `self.kernel_manager_class.start_kernel()`. Because
            that defaults to KernelManager, this will likely include options
            accepted by `KernelManager.start_kernel()``, which includes `cwd`.

        Returns
        -------
        km : KernelManager
            A kernel manager as created by self.kernel_manager_class.
        kc : KernelClient
            Kernel client as created by the kernel manager `km`.
        """
        km = self.kernel_manager_class(kernel_name=self.kernel_name,
                                       config=self.config)
        km.start_kernel(extra_arguments=self.extra_arguments, **kwargs)

        kc = km.client()
        kc.start_channels()
        try:
            kc.wait_for_ready(timeout=self.startup_timeout)
        except RuntimeError:
            kc.stop_channels()
            km.shutdown_kernel()
            raise
        kc.allow_stdin = False
        return km, kc

    @contextmanager
    def setup_preprocessor(self, nb, resources, km=None):
        """
        Context manager for setting up the class to execute a notebook.

        The assigns `nb` to `self.nb` where it will be modified in-place. It also creates
        and assigns the Kernel Manager (`self.km`) and Kernel Client(`self.kc`).

        It is intended to yield to a block that will execute codeself.

        When control returns from the yield it stops the client's zmq channels, shuts
        down the kernel, and removes the now unused attributes.

        Parameters
        ----------
        nb : NotebookNode
            Notebook being executed.
        resources : dictionary
            Additional resources used in the conversion process. For example,
            passing ``{'metadata': {'path': run_path}}`` sets the
            execution path to ``run_path``.
        km : KernerlManager (optional)
            Optional kernel manaher. If none is provided, a kernel manager will
            be created.

        Returns
        -------
        nb : NotebookNode
            The executed notebook.
        resources : dictionary
            Additional resources used in the conversion process.
        """
        path = resources.get('metadata', {}).get('path', '') or None
        self.nb = nb
        # clear display_id map
        self._display_id_map = {}

        if km is None:
            self.km, self.kc = self.start_new_kernel(cwd=path)
            try:
                # Yielding unbound args for more easier understanding and downstream consumption
                yield nb, self.km, self.kc
            finally:
                self.kc.stop_channels()
                self.km.shutdown_kernel(now=self.shutdown_kernel == 'immediate')

                for attr in ['nb', 'km', 'kc']:
                    delattr(self, attr)
        else:
            self.km = km
            if not km.has_kernel:
                km.start_kernel(extra_arguments=self.extra_arguments, **kwargs)
            self.kc = km.client()

            self.kc.start_channels()
            try:
                self.kc.wait_for_ready(timeout=self.startup_timeout)
            except RuntimeError:
                self.kc.stop_channels()
                raise
            self.kc.allow_stdin = False
            try:
                yield nb, self.km, self.kc
            finally:
                for attr in ['nb', 'km', 'kc']:
                    delattr(self, attr)

    def preprocess(self, nb, resources, km=None):
        """
        Preprocess notebook executing each code cell.

        The input argument `nb` is modified in-place.

        Parameters
        ----------
        nb : NotebookNode
            Notebook being executed.
        resources : dictionary
            Additional resources used in the conversion process. For example,
            passing ``{'metadata': {'path': run_path}}`` sets the
            execution path to ``run_path``.
        km: KernelManager (optional)
            Optional kernel manager. If none is provided, a kernel manager will
            be created.

        Returns
        -------
        nb : NotebookNode
            The executed notebook.
        resources : dictionary
            Additional resources used in the conversion process.
        """

        with self.setup_preprocessor(nb, resources, km=km):
            self.log.info("Executing notebook with kernel: %s" % self.kernel_name)
            nb, resources = super(ExecutePreprocessor, self).preprocess(nb, resources)
            info_msg = self._wait_for_reply(self.kc.kernel_info())
            nb.metadata['language_info'] = info_msg['content']['language_info']

        return nb, resources

    def preprocess_cell(self, cell, resources, cell_index):
        """
        Executes a single code cell. See base.py for details.

        To execute all cells see :meth:`preprocess`.
        """
        if cell.cell_type != 'code' or not cell.source.strip():
            return cell, resources

        reply, outputs = self.run_cell(cell, cell_index)
        cell.outputs = outputs

        cell_allows_errors = (self.allow_errors or "raises-exception"
                              in cell.metadata.get("tags", []))

        if self.force_raise_errors or not cell_allows_errors:
            for out in outputs:
                if out.output_type == 'error':
                    raise CellExecutionError.from_cell_and_msg(cell, out)
            if (reply is not None) and reply['content']['status'] == 'error':
                raise CellExecutionError.from_cell_and_msg(cell, reply['content'])
        return cell, resources

    def _update_display_id(self, display_id, msg):
        """Update outputs with a given display_id"""
        if display_id not in self._display_id_map:
            self.log.debug("display id %r not in %s", display_id, self._display_id_map)
            return

        if msg['header']['msg_type'] == 'update_display_data':
            msg['header']['msg_type'] = 'display_data'

        try:
            out = output_from_msg(msg)
        except ValueError:
            self.log.error("unhandled iopub msg: " + msg['msg_type'])
            return

        for cell_idx, output_indices in self._display_id_map[display_id].items():
            cell = self.nb['cells'][cell_idx]
            outputs = cell['outputs']
            for output_idx in output_indices:
                outputs[output_idx]['data'] = out['data']
                outputs[output_idx]['metadata'] = out['metadata']

    def _wait_for_reply(self, msg_id, cell=None):
        # wait for finish, with timeout
        while True:
            try:
                if self.timeout_func is not None and cell is not None:
                    timeout = self.timeout_func(cell)
                else:
                    timeout = self.timeout

                if not timeout or timeout < 0:
                    timeout = None
                msg = self.kc.shell_channel.get_msg(timeout=timeout)
            except Empty:
                self.log.error(
                    "Timeout waiting for execute reply (%is)." % self.timeout)
                if self.interrupt_on_timeout:
                    self.log.error("Interrupting kernel")
                    self.km.interrupt_kernel()
                    break
                else:
                    try:
                        exception = TimeoutError
                    except NameError:
                        exception = RuntimeError
                    raise exception("Cell execution timed out")

            if msg['parent_header'].get('msg_id') == msg_id:
                return msg
            else:
                # not our reply
                continue

    def run_cell(self, cell, cell_index=0):
        msg_id = self.kc.execute(cell.source)
        self.log.debug("Executing cell:\n%s", cell.source)
        exec_reply = self._wait_for_reply(msg_id, cell)

        outs = cell.outputs = []

        while True:
            try:
                # We've already waited for execute_reply, so all output
                # should already be waiting. However, on slow networks, like
                # in certain CI systems, waiting < 1 second might miss messages.
                # So long as the kernel sends a status:idle message when it
                # finishes, we won't actually have to wait this long, anyway.
                msg = self.kc.iopub_channel.get_msg(timeout=self.iopub_timeout)
            except Empty:
                self.log.warning("Timeout waiting for IOPub output")
                if self.raise_on_iopub_timeout:
                    raise RuntimeError("Timeout waiting for IOPub output")
                else:
                    break
            if msg['parent_header'].get('msg_id') != msg_id:
                # not an output from our execution
                continue

            msg_type = msg['msg_type']
            self.log.debug("output: %s", msg_type)
            content = msg['content']

            # set the prompt number for the input and the output
            if 'execution_count' in content:
                cell['execution_count'] = content['execution_count']

            if msg_type == 'status':
                if content['execution_state'] == 'idle':
                    break
                else:
                    continue
            elif msg_type == 'execute_input':
                continue
            elif msg_type == 'clear_output':
                outs[:] = []
                # clear display_id mapping for this cell
                for display_id, cell_map in self._display_id_map.items():
                    if cell_index in cell_map:
                        cell_map[cell_index] = []
                continue
            elif msg_type.startswith('comm'):
                continue

            display_id = None
            if msg_type in {'execute_result', 'display_data', 'update_display_data'}:
                display_id = msg['content'].get('transient', {}).get('display_id', None)
                if display_id:
                    self._update_display_id(display_id, msg)
                if msg_type == 'update_display_data':
                    # update_display_data doesn't get recorded
                    continue

            try:
                out = output_from_msg(msg)
            except ValueError:
                self.log.error("unhandled iopub msg: " + msg_type)
                continue
            if display_id:
                # record output index in:
                #   _display_id_map[display_id][cell_idx]
                cell_map = self._display_id_map.setdefault(display_id, {})
                output_idx_list = cell_map.setdefault(cell_index, [])
                output_idx_list.append(len(outs))

            outs.append(out)

        return exec_reply, outs


def executenb(nb, cwd=None, km=None, **kwargs):
    """Execute a notebook's code, updating outputs within the notebook object.

    This is a convenient wrapper around ExecutePreprocessor. It returns the
    modified notebook object.

    Parameters
    ----------
    nb : NotebookNode
      The notebook object to be executed
    cwd : str, optional
      If supplied, the kernel will run in this directory
    km : KernelManager, optional
      If supplied, the specified kernel manager will be used for code execution.
    kwargs :
      Any other options for ExecutePreprocessor, e.g. timeout, kernel_name
    """
    resources = {}
    if cwd is not None:
        resources['metadata'] = {'path': cwd}
    ep = ExecutePreprocessor(**kwargs)
    return ep.preprocess(nb, resources, km=km)[0]
