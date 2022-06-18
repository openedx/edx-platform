"""
This script will process logs generated from CookieMonitoringMiddleware.

Sample usage::

    python edx_django_utils/monitoring/scripts/process_cookie_monitoring_logs.py --csv_input large-cookie-logs.csv

Or for more details::

    python edx_django_utils/monitoring/scripts/process_cookie_monitoring_logs.py --help

"""
import csv
import logging
import re

import click
from dateutil import parser

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)


# Note: Not all Open edX deployments will be affected by the same third-party cookies,
#   but it is ok to have some of these cookies go unused.
PARAMETERIZED_COOKIES = [
    (re.compile(r"_gac_UA-(\d|-)+"), "_gac_UA-{id}"),
    (re.compile(r"_hjSession_\d+"), "_hjSession_{id}"),
    (re.compile(r"_hjSessionUser_\d+"), "_hjSessionUser_{id}"),
    (re.compile(r"ab\.storage\.deviceId\..*"), "ab.storage.deviceId.{id}"),
    (re.compile(r"ab\.storage\.sessionId\..*"), "ab.storage.deviceId.{id}"),
    (re.compile(r"ab\.storage\.userId\..*"), "ab.storage.userId.{id}"),
    (re.compile(r"AMCV_\w+%40AdobeOrg"), "AMCV_{id}@AdobeOrg"),
    (re.compile(r"amplitude_id_.*"), "amplitude_id_{id}"),
    (re.compile(r"mp_\w+_mixpanel"), "mp_{id}_mixpanel"),
]


@click.command()
@click.option(
    "--csv_input",
    help="File name of .csv file with Splunk logs for large cookie headers.",
    required=True
)
def main(csv_input):
    """
    Reads CSV of large cookie logs and processes and provides summary output.

    Expected CSV format (from Splunk export searching on "BEGIN-COOKIE-SIZES"):

        \b
        _raw,_time,index,
        ...

    """
    cookie_headers = _load_csv(csv_input)
    processed_cookie_headers = process_cookie_headers(cookie_headers)
    print_processed_cookies(processed_cookie_headers)


def _load_csv(csv_file):
    """
    Reads CSV of large cookie data and returns a dict of details.

    Arguments:
        csv_file (string): File name for the csv

    Returns a list of dicts containing parsed details for each cookie header log entry.

    """
    with open(csv_file) as file:
        csv_data = file.read()
    reader = csv.DictReader(csv_data.splitlines())

    # Regex to match against log messages like the following:
    #   BEGIN-COOKIE-SIZES(total=3773) user-info: 903, csrftoken: 64, ... END-COOKIE-SIZES
    cookie_log_regex = re.compile(r"BEGIN-COOKIE-SIZES\(total=(?P<total>\d+)\)(?P<cookie_sizes>.*)END-COOKIE-SIZES")
    # Regex to match against just a single size, like the following:
    #   csrftoken: 64
    cookie_size_regex = re.compile(r"(?P<name>.*): (?P<size>\d+)")

    cookie_headers = []
    for row in reader:
        cookie_header_sizes = {}

        raw_cookie_log = row.get("_raw")
        cookie_begin_count = raw_cookie_log.count("BEGIN-COOKIE-SIZES")
        if cookie_begin_count == 0:
            logging.info("No BEGIN-COOKIE-SIZES delimiter found. Skipping row.")
        elif cookie_begin_count > 1:
            # Note: this wouldn't parse correctly right now, and it isn't worth coding for.
            logging.warning("Multiple cookie entries found in same row. Skipping row.")
            continue
        match = cookie_log_regex.search(raw_cookie_log)
        if not match:
            logging.error("Malformed cookie entry. Skipping row.")
            continue

        cookie_header_size = int(match.group("total"))
        if cookie_header_size == 0:
            continue

        cookie_sizes_str = match.group("cookie_sizes").strip()

        cookie_sizes = cookie_sizes_str.split(", ")
        for cookie_size in cookie_sizes:
            match = cookie_size_regex.search(cookie_size)
            if not match:
                logging.error(f"Could not parse cookie size from: {cookie_size}")
                continue
            cookie_header_sizes[match.group("name")] = int(match.group("size"))

        cookie_header_size_computed = max(
            0, sum(len(name) + size + 3 for (name, size) in cookie_header_sizes.items()) - 2
        )

        cookie_headers.append({
            "datetime": parser.parse(row.get("_time")),
            "env": row.get("index"),
            "cookie_header_size": cookie_header_size,
            "cookie_header_size_computed": cookie_header_size_computed,
            "cookie_sizes": cookie_header_sizes,
        })

    return cookie_headers


def process_cookie_headers(cookie_headers):
    """
    Process the parsed cookie header log entries.

    Arguments:
        cookie_headers: a list of dicts containing parsed details.

    Returns a dict of processed cookies.
    """
    processed_cookies = {}
    for cookie_header in cookie_headers:
        for (name, size) in cookie_header["cookie_sizes"].items():

            # Replace parameterized cookies. For example:
            #   _hjSessionUser_111111 => _hjSessionUser_{id}
            for (regex, replacement_name) in PARAMETERIZED_COOKIES:
                if regex.fullmatch(name):
                    logging.debug(f"Replacing {name} with {replacement_name}.")
                    name = replacement_name
                    break

            processed_cookie = processed_cookies.get(name, {})

            # compute the full size each cookie takes up in the cookie header, including name and delimiters
            full_size = len(name) + size + 3
            set_max_attribute(processed_cookie, "max_full_size", full_size)
            set_min_attribute(processed_cookie, "min_full_size", full_size)

            set_max_attribute(processed_cookie, "max_size", size)
            set_min_attribute(processed_cookie, "min_size", size)

            processed_cookie["count"] = processed_cookie.get("count", 0) + 1

            # Note: The following details relate to the header, and not to the specific cookie.
            #   This may give a quick view of cookies associated with the largest header, or the
            #   header with the most cookies.

            set_max_attribute(processed_cookie, "last_seen", cookie_header["datetime"])
            set_min_attribute(processed_cookie, "first_seen", cookie_header["datetime"])

            set_max_attribute(processed_cookie, "max_cookie_count", len(cookie_header["cookie_sizes"]))
            set_min_attribute(processed_cookie, "min_cookie_count", len(cookie_header["cookie_sizes"]))
            set_max_attribute(processed_cookie, "max_header_size", cookie_header["cookie_header_size"])
            set_min_attribute(processed_cookie, "min_header_size", cookie_header["cookie_header_size"])
            # Note: skipping cookie_header_size_calculated unless we see a need for it.

            processed_cookie["envs"] = processed_cookie.get("envs", set())
            processed_cookie["envs"].add(cookie_header["env"])

            processed_cookies[name] = processed_cookie

    return processed_cookies


def set_min_attribute(processed_cookie, key, value):
    """
    Sets processed_cookie[key] to the smaller of value and its current value.
    """
    processed_cookie[key] = min(value, processed_cookie.get(key, value))


def set_max_attribute(processed_cookie, key, value):
    """
    Sets processed_cookie[key] to the larger of value and its current value.
    """
    processed_cookie[key] = max(value, processed_cookie.get(key, value))


def print_processed_cookies(processed_cookies):
    """
    Output processed cookie information.
    """
    sorted_cookie_items = sorted(processed_cookies.items(), key=lambda x: x[1]["max_full_size"], reverse=True)
    print("name,max_full_size,min_full_size,max_size,min_size,count,"
          "last_seen,first_seen,max_cookie_count,min_cookie_count,max_header_size,min_header_size,envs")
    for (name, data) in sorted_cookie_items:
        print(f'{name},{data["max_full_size"]},{data["min_full_size"]},'
              f'{data["max_size"]},{data["min_size"]},{data["count"]},'
              f'{data["last_seen"]},{data["first_seen"]},'
              f'{data["max_cookie_count"]},{data["min_cookie_count"]},'
              f'{data["max_header_size"]},{data["min_header_size"]},'
              f'"{",".join(sorted(data["envs"]))}"')


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
