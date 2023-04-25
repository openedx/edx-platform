"""
An importlinter contract that can flag imports of private APIs
"""

from importlinter import Contract, ContractCheck, fields, output


class IsolatedAppsContract(Contract):
    """
    Contract that defines most of an 'app' (python package) as private, and
    ensures that python code outside of the package doesn't import anything
    other than the public API defined in the package's `api.py` file.
    """
    isolated_apps = fields.ListField(subfield=fields.StringField())
    # List of allowed modules (like ["api", "urls"] to allow "import x.api")
    allowed_modules = fields.ListField(subfield=fields.StringField())

    def check(self, graph, verbose):
        forbidden_imports_found = []

        for package in self.isolated_apps:
            output.verbose_print(
                verbose,
                f"Getting import details for anything that imports {package}..."
            )
            modules = graph.find_descendants(package)
            for module in modules:
                # We have a list of modules like "api.py" that *are* allowed to be imported from anywhere:
                for allowed_module in self.allowed_modules:
                    if module.endswith(f".{allowed_module}"):
                        break
                else:
                    # See who is importing this:
                    importers = graph.find_modules_that_directly_import(module)
                    for importer in importers:
                        if importer.startswith(package):
                            continue  # Ignore imports from within the same package
                        # Add this import to our list of contract violations:
                        import_details = graph.get_import_details(importer=importer, imported=module)
                        for import_detail in import_details:
                            forbidden_imports_found.append({**import_detail, "package": package})

        return ContractCheck(
            kept=not bool(forbidden_imports_found),
            metadata={
                'forbidden_imports_found': forbidden_imports_found,
            }
        )

    def render_broken_contract(self, check):
        for details in check.metadata['forbidden_imports_found']:
            package = details['package']
            importer = details['importer']
            line_number = details['line_number']
            line_contents = details['line_contents']
            output.print_error(f'{importer}:{line_number}: imported from non-public API of {package}:')
            output.indent_cursor()
            output.print_error(line_contents)
            output.new_line()
