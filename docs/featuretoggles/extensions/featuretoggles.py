import os

from docutils import nodes
from docutils.parsers.rst import Directive
import yaml

REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "report.yml")


def load_feature_toggles(report_path):
    """ Load the feature toggles listed in the report file.
    Return:
        toggles (dict): feature toggles indexed by name.
    """
    with open(report_path) as report_file:
        report = yaml.safe_load(report_file)

    group_id_names = {}
    toggles = {}
    for entries in report.values():
        for entry in entries:
            group_id = entry["report_group_id"]
            key = entry["annotation_token"]
            value = entry["annotation_data"]
            if key == ".. toggle_name:":
                toggle_name = value
                group_id_names[group_id] = toggle_name
                toggles[toggle_name] = {
                    "filename": entry["filename"],
                    "line_number": entry["line_number"],
                }
            else:
                toggles[group_id_names[group_id]][key] = value

    return toggles


class FeatureToggles(Directive):
    """
    This class requires the presence of a report.yml file in the parent folder.

    TODO: improve this docstring
    """

    REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "report.yml")

    def run(self):
        toggle_nodes = list(self.iter_nodes())
        # import ipdb; ipdb.set_trace()
        return [nodes.section("", *toggle_nodes, ids=["featuretoggles"])]

    def iter_nodes(self):
        toggles = load_feature_toggles(self.REPORT_PATH)
        # paragraph = nodes.paragraph(text=sorted(toggles)[0])
        # list_item = nodes.list_item(children=[paragraph])
        for toggle_name in sorted(toggles):
            # toggle_attributes = toggles[toggle_name]
            toggle = toggles[toggle_name]
            yield nodes.title(text=toggle_name)
            yield nodes.paragraph(
                text="Default: {}".format(
                    toggle.get(".. toggle_default:", "Not defined")
                )
            )
            yield nodes.paragraph(
                "",
                "Source: ",
                nodes.reference(
                    text="{} (line {})".format(
                        toggle["filename"], toggle["line_number"]
                    ),
                    refuri="{}/blob/{}/{}#L{}".format(
                        # TODO make it possible to configure repo url to use this extension with different IDAs
                        "https://github.com/edx/edx-platform",
                        # TODO: make it possible to configure the repo version -- via OPENEDX_RELEASE environment value?
                        "master",
                        toggle["filename"],
                        toggle["line_number"],
                    ),
                ),
            )
            yield nodes.paragraph(text=toggle.get(".. toggle_description:", ""))


def setup(app):
    app.add_directive("featuretoggles", FeatureToggles)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
