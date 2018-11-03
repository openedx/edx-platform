from nbgrader.plugins.export import ExportPlugin

class MyExporter(ExportPlugin):
    def export(self, gradebook):
        with open(self.to, "w") as fh:
            fh.write("hello!")
