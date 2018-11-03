from nbconvert.preprocessors import ExecutePreprocessor
from traitlets import Bool, List, Integer
from textwrap import dedent

from . import NbGraderPreprocessor

class UnresponsiveKernelError(Exception):
    pass


class Execute(NbGraderPreprocessor, ExecutePreprocessor):

    interrupt_on_timeout = Bool(True)
    allow_errors = Bool(True)
    raise_on_iopub_timeout = Bool(True)
    extra_arguments = List([], help=dedent(
        """
        A list of extra arguments to pass to the kernel. For python kernels,
        this defaults to ``--HistoryManager.hist_file=:memory:``. For other
        kernels this is just an empty list.
        """)
    ).tag(config=True)

    execute_retries = Integer(0, help=dedent(
        """
        The number of times to try re-executing the notebook before throwing
        an error. Generally, this shouldn't need to be set, but might be useful
        for CI environments when tests are flaky.
        """)
    ).tag(config=True)

    def preprocess(self, nb, resources, retries=None):
        kernel_name = nb.metadata.get('kernelspec', {}).get('name', 'python')
        if self.extra_arguments == [] and kernel_name == "python":
            self.extra_arguments = ["--HistoryManager.hist_file=:memory:"]

        if retries is None:
            retries = self.execute_retries

        try:
            output = super(Execute, self).preprocess(nb, resources)
        except RuntimeError:
            if retries == 0:
                raise UnresponsiveKernelError()
            else:
                self.log.warning("Failed to execute notebook, trying again...")
                return self.preprocess(nb, resources, retries=retries - 1)

        return output
