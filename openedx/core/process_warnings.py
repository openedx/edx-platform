import json
import os
import pprint
import re
import pdb
import argparse
from write_to_html import HtmlOutlineWriter

pp = pprint.PrettyPrinter(indent=4, depth=2)


def seperate_warnings_by_location(warnings_data):
    """
    Warnings originate from multiple locations, this function takes in list of warning objects 
    and seperates them based on their filename location
    """

    # first create regex for each know file location
    warnings_locations = {
        ".*/python\d\.\d/site-packages/.*\.py": "python",
        ".*/edx-platform/lms/.*\.py": "lms",
        ".*/edx-platform/openedx/.*\.py": "openedx",
        ".*/edx-platform/cms/.*\.py": "cms",
        ".*/edx-platform/common/.*\.py": "common",
    }

    # create datatypes to hold location: dictionary with values that are lists(to store warning objects)
    warnings_by_location = {}
    for location in warnings_locations.values():
        warnings_by_location[location] = []
    # creating list for any warnings not covered by above locations
    warnings_by_location["other"] = []

    """
    seperate into locations
    flow:
     iterate through each wanring_object, see if its filename matches any regex in warning locations.
     If so, add it to appropriate list in warnings_by_location
    """
    for warnings_object in warnings_data:
        warning_origin_located = False
        for key in warnings_locations:
            if re.search(key, warnings_object["filename"]) != None:
                warnings_by_location[warnings_locations[key]].append(warnings_object)
                warning_origin_located = True
                break
        if not warning_origin_located:
            warnings_by_location["other"].append(warnings_object)
    return warnings_by_location


def read_warning_data(dir_path):
    """
    During test runs in jenkins, multiple warning json files are output. This function finds all files
    and aggregates the warnings in to one large list
    """
    # pdb.set_trace()
    dir_path = os.path.expanduser(dir_path)
    # find all files that exist in given directory
    files_in_dir = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    warnings_files = []

    # TODO(jinder): currently this is hardcoded in, maybe create a constants file with info
    # THINK(jinder): but creating file for one constant seems overkill
    warnings_file_name_regex = "pytest_warnings_?\d*\.json"

    # iterate through files_in_dir and see if they match our know file name pattern
    for file in files_in_dir:
        if re.search(warnings_file_name_regex, file) != None:
            warnings_files.append(file)

    # go through each warning file and aggregate warnigns into warnings_data
    warnings_data = []
    for file in warnings_files:
        with open(os.path.expanduser(dir_path + "/" + file), "r") as read_file:
            json_input = json.load(read_file)
            if "warnings" in json_input:
                data = json_input["warnings"]
                warnings_data.extend(data)
            else:
                print(file)
    return warnings_data


def compress_similar_warnings(warnings):
    """
        During pytest run, multiple instances of warnings are output
        This function creates set of unique warnings(based on both warning text and filename)
        and outputs dict : {warning text:[filename:warning_object]}
        It also adds num(number of same warnings found) to keys in warning object
    """

    # first create additional data sturts to make iterating through warning objects easier
    # list of just warning texts and index of given warning
    warnings_text = []
    # list of all unique warning texts
    warnings_text_set = set()
    for index, dict_obj in enumerate(warnings):
        warnings_text.append((index, dict_obj["message"]))
        warnings_text_set.add(dict_obj["message"])
    """
    For each unique warning text, find all occurences of it in warnings. Seperate by filename
    and count number of times warning occurs
    POSSIBLE ERROR: Currently this assumes warning is only output in one line in file
    """
    output = {}
    for warning_text in warnings_text_set:
        output[warning_text] = []
        for index, warning_message in warnings_text:
            if warning_message == warning_text:
                output[warning_text].append(warnings[index])
        # before removing duplcates, count number of times they occur
        count = {}
        for d in output[warning_text]:
            if d["filename"] in count:
                count[d["filename"]]["num"] += 1
            else:
                count[d["filename"]] = {"num": 1, "warning": d}
        for d in count:
            count[d]["warning"]["num"] = count[d]["num"]
        output[warning_text] = [count[d]["warning"] for d in count]
        # pdb.set_trace()
    return output


def process_warnings_json(dir_path):
    """
    Master function to process through all warnings and output a dict

    dict structure:
    {
        location: [{warning text: {file_name: warning object}}]
    }

    flow:
        Aggregate data from all warning files
        Seperate warnings by deprecated vs non deprecated(has word deprecate in it)
        Further categorize warnings
        Return output
    Possible Error/enchancement: there might be better ways to seperate deprecates vs
        non-deprecated warnings
    """
    warnings_data = read_warning_data(dir_path)
    deprecated_warnings = []
    non_deprecated_warnings = []
    for warnings_object in warnings_data:
        if "deprecated" in warnings_object["message"]:
            deprecated_warnings.append(warnings_object)
        else:
            non_deprecated_warnings.append(warnings_object)
    deprecated_output_json = seperate_warnings_by_location(deprecated_warnings)
    output = {}
    for k, v in deprecated_output_json.items():
        output[k] = compress_similar_warnings(v)
    return output


def sort_by_count(warnings_object):
    temp_location_list = []
    for location in warnings_object:
        temp_warning_text_list = []
        for warning_text in warnings_object[location]:
            sorted_warnings = sorted(warnings_object[location][warning_text], key = lambda warning: -1*warning["num"])
            num = sum([warning["num"] for warning in sorted_warnings])
            temp_warning_text_list.append( (warning_text, sorted_warnings, num))
        sorted_warning_texts = sorted(temp_warning_text_list, key = lambda warning_text_object: -1 * warning_text_object[-1])
        num = sum([warning_text_object[-1] for warning_text_object in sorted_warning_texts])
        temp_location_list.append([location, sorted_warning_texts, num])
    sorted_locations = sorted(temp_location_list, key= lambda location_object: -1 * location_object[-1])          
    return sorted_locations


def write_html_report(warnings_object, html_path):
    """warning_object structured like:
        {locations: { warning_texts:[warnings objects]}
        }
    """
    html_path = os.path.expanduser(html_path)
    with open(html_path, "w") as fout:
        html_writer = HtmlOutlineWriter(fout)
        for location in warnings_object:
            html = u'<span class="count">{location}</span> '.format(location=location)
            html_writer.start_section(html, klass="location")
            for warning_text in warnings_object[location]:
                html = u'<span class="count">{warning_text}</span> '.format(
                    warning_text=warning_text
                )
                html_writer.start_section(html, klass="warning_text")
                # warnings_object[location][warning_text] is a list
                for warning in warnings_object[location][warning_text]:
                    html = u'<span class="count">{warning_file_path}</span> '.format(
                        warning_file_path=warning["filename"]
                    )
                    html_writer.start_section(html, klass="warning")

                    html = u'<p class="lineno">lineno: {lineno}</p> '.format(
                        lineno=warning["lineno"]
                    )
                    html_writer.write(html)
                    html = u'<p class="num">num_occur: {num}</p> '.format(
                        num=warning["num"]
                    )
                    html_writer.write(html)

                    html_writer.end_section()
                html_writer.end_section()
            html_writer.end_section()


def write_html_report_sorted_warnings(sorted_warnings_object, html_path):
    """warning_object structured like:
        {locations: { warning_texts:[warnings objects]}
        }
    """
    html_path = os.path.expanduser(html_path)
    with open(html_path, "w") as fout:
        html_writer = HtmlOutlineWriter(fout)
        for location in sorted_warnings_object:
            pp.pprint(location)
            html = u'<span class="count">{location}, count: {count}</span> '.format(location=location[0],count=location[-1])
            html_writer.start_section(html, klass="location")
            for warning_text in location[1]:
                pp.pprint(warning_text)
                html = u'<span class="count">{warning_text}, count: {count}</span> '.format(
                    warning_text=warning_text[0], count=warning_text[-1]
                )
                html_writer.start_section(html, klass="warning_text")
                # warnings_object[location][warning_text] is a list
                for warning in warning_text[1]:
                    pp.pprint(warning)
                    html = u'<span class="count">{warning_file_path}</span> '.format(
                        warning_file_path=warning["filename"]
                    )
                    html_writer.start_section(html, klass="warning")

                    html = u'<p class="lineno">lineno: {lineno}</p> '.format(
                        lineno=warning["lineno"]
                    )
                    html_writer.write(html)
                    html = u'<p class="num">num_occur: {num}</p> '.format(
                        num=warning["num"]
                    )
                    html_writer.write(html)

                    html_writer.end_section()
                html_writer.end_section()
            html_writer.end_section()


parser = argparse.ArgumentParser(
    description="Process and categorize pytest warnings and output html report."
)
parser.add_argument("--dir_path", default="test_root/log")
parser.add_argument("--html_path", default="test_html.html")
args = parser.parse_args()
print(args)
output = process_warnings_json(args.dir_path)
sorted_output = sort_by_count(output)
write_html_report_sorted_warnings(sorted_output, args.html_path)
# write_html_report(output, args.html_path)
