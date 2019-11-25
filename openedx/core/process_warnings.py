import json
import os
import pprint
import re
import pdb
from write_to_html import HtmlOutlineWriter

pp = pprint.PrettyPrinter(indent=4, depth=2)

def seperate_warnings_by_location(warnings_data):
    warnings_locations = {".*/python\d\.\d/site-packages/.*\.py":"python",  ".*/edx-platform/lms/.*\.py":"lms", ".*/edx-platform/openedx/.*\.py":"openedx", ".*/edx-platform/cms/.*\.py": "cms", ".*/edx-platform/common/.*\.py":"common"}
    warnings_by_location = {}
    for location in warnings_locations.values():
        warnings_by_location[location] = []
    # creating list for any warnings not covered by above locations
    warnings_by_location['other'] = []
    for warnings_object in warnings_data:
        warning_origin_located = False
        for key in warnings_locations:
            if re.search(key, warnings_object['filename']) != None:
                warnings_by_location[warnings_locations[key]].append(warnings_object)
                warning_origin_located = True
                break
        if not warning_origin_located:
            warnings_by_location['other'].append(warnings_object)
    return warnings_by_location

def read_warning_data(path):
    dir_path = os.path.expanduser("~/dev/edx-platform/test_root/log")
    dir_path = os.path.expanduser(path)
    files_in_dir = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    warnings_files = []
    warnings_file_name_regex = "warnings_?\d*\.json"
    for file in files_in_dir:
        if re.search(warnings_file_name_regex, file) != None:
            warnings_files.append(file)

    warnings_data = []
    for file in warnings_files:
        with open(os.path.expanduser(path + "/" + file),"r") as read_file:
            data = json.load(read_file)["warnings"]
            warnings_data.extend(data)
    return warnings_data

def compress_similar_warnings(warnings):
    warnings_text = []
    warnings_text_set = set()
    for index, dict_obj in enumerate(warnings):
        warnings_text.append((index, dict_obj["message"]))
        warnings_text_set.add(dict_obj["message"])
    output = {}
    for warning_text in warnings_text_set:
        output[warning_text] = []
        for index, warning_message in warnings_text:
            if warning_message == warning_text:
                output[warning_text].append(warnings[index])
        #removing duplicates
        count = {}
        for d in output[warning_text]:
            pp.pprint(d["filename"])
            if d["filename"] in count:
                count[d["filename"]]["num"] +=1
            else:
                count[d["filename"]] = {"num": 1, "warning": d}
        pdb.set_trace()
        for d in count:
            count[d]["warning"]["num"] = count[d]["num"]
        output[warning_text] = [count[d]["warning"] for d in count]
    return output



def process_warnings_json(path):
    warnings_data = read_warning_data(path)
    deprecated_warnings = []
    non_deprecated_warnings = []
    for warnings_object in warnings_data:
        if "deprecated" in warnings_object['message']:
            deprecated_warnings.append(warnings_object)
        else:
            non_deprecated_warnings.append(warnings_object)
    deprecated_output_json = seperate_warnings_by_location(deprecated_warnings)
    output = {}
    for k, v in deprecated_output_json.items():
        output[k] = compress_similar_warnings(v)
    return output

def write_html_report(warnings_object):
    """warning_object structured like:
        {locations: { warning_texts:[warnings objects]}
        }
    """
    with open("text_html.html", "w") as fout:
        html_writer = HtmlOutlineWriter(fout)
        for location in warnings_object:
            html = u'<span class="count">{location}:</span> '.format(location=location)
            html_writer.start_section(html, klass="location")
            for warning_text in warnings_object[location]:
                html = u'<span class="count">{warning_text}:</span> '.format(
                    warning_text=warning_text)
                html_writer.start_section(html, klass="warning_text")
                # warnings_object[location][warning_text] is a list
                for warning in warnings_object[location][warning_text]:
                    html = u'<span class="count">{warning_file_path}:</span> '.format(
                    warning_file_path=warning["filename"])
                    html_writer.start_section(html, klass="warning")
                    
                    html = u'<p class="lineno">lineno: {lineno}:</p> '.format(
                    lineno=warning["lineno"])
                    html_writer.write(html)
                    html = u'<p class="num">num_occur: {num}:</p> '.format(
                    num=warning["num"])
                    html_writer.write(html)

                    html_writer.end_section()
                html_writer.end_section()
            html_writer.end_section()







dir_path = "~/dev/edx-platform/test_root/log"
dir_path = "~/Downloads/log"
output = process_warnings_json(dir_path)
write_html_report(output)


