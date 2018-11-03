from . import NbGraderPreprocessor

from traitlets import Integer

class LimitOutput(NbGraderPreprocessor):
    """Preprocessor for limiting cell output"""

    max_lines = Integer(
        1000,
        help="maximum number of lines of output (-1 means no limit)"
    ).tag(config=True)

    max_traceback = Integer(
        100,
        help="maximum number of traceback lines (-1 means no limit)"
    ).tag(config=True)

    def _limit_stream_output(self, cell):
        if self.max_lines == -1 or cell.cell_type != "code":
            return cell

        length = 0
        new_outputs = []
        for output in cell.outputs:
            if output.output_type == 'stream':
                if length == self.max_lines:
                    continue

                text = output.text.split("\n")
                if (len(text) + length) > self.max_lines:
                    text = text[:(self.max_lines - length - 1)]
                    text.append("... Output truncated ...")

                length += len(text)
                output.text = "\n".join(text)

            new_outputs.append(output)

        cell.outputs = new_outputs
        return cell

    def _limit_traceback(self, cell):
        if self.max_traceback == -1 or cell.cell_type != "code":
            return cell

        for output in cell.outputs:
            if output.output_type == "error":
                if len(output.traceback) > self.max_traceback:
                    start = int(self.max_traceback / 2)
                    end = self.max_traceback - start - 1
                    tb = output.traceback[:start]
                    tb.append("... Traceback truncated ...")
                    tb.extend(output.traceback[-end:])
                    output.traceback = tb

        return cell

    def preprocess_cell(self, cell, resources, cell_index):
        cell = self._limit_stream_output(cell)
        cell = self._limit_traceback(cell)
        return cell, resources
