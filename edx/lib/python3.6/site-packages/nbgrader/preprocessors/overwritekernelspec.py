import json

from . import NbGraderPreprocessor
from ..api import Gradebook


class OverwriteKernelspec(NbGraderPreprocessor):
    """A preprocessor for checking the notebook kernelspec metadata."""

    def preprocess(self, nb, resources):
        # pull information from the resources
        notebook_id = resources['nbgrader']['notebook']
        assignment_id = resources['nbgrader']['assignment']
        db_url = resources['nbgrader']['db_url']

        with Gradebook(db_url) as gb:
            kernelspec = json.loads(
                gb.find_notebook(notebook_id, assignment_id).kernelspec)
            self.log.debug("Source notebook kernelspec: {}".format(kernelspec))
            self.log.debug(
                "Submitted notebook kernelspec: {}"
                "".format(nb.metadata.get('kernelspec', None))
            )
            if kernelspec:
                self.log.debug(
                    "Overwriting submitted notebook kernelspec: {}"
                    "".format(kernelspec)
                )
                nb.metadata['kernelspec'] = kernelspec
        return nb, resources
