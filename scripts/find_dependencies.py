"""
Spider and catalog dependencies.

$ export OLIVE_DIRS=$(gittreeif origin/open-release/olive.master -q pwd)
$ python find_deps.py $OLIVE_DIRS

"""

import concurrent.futures
import contextlib
import functools
import itertools
import json
import os
import re
import requirements
import shlex
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path
from typing import Iterable, Optional, Tuple

import requests
from rich.progress import Progress, MofNCompleteColumn

# pylint: disable=unspecified-encoding

cached = functools.lru_cache(maxsize=0)

@contextlib.contextmanager
def change_dir(new_dir):
    """
    Change to a new directory, and then change back.

    Will make the directory if needed.
    """
    old_dir = os.getcwd()
    new_dir = Path(new_dir)
    new_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(new_dir)
    try:
        yield new_dir
    finally:
        os.chdir(old_dir)


def run_command(cmd: str, outfile=None) -> Tuple[bool, str]:
    """
    Run a command line (with no shell).  Write the output to a file.

    Returns a tuple:
        bool: true if the command succeeded.
        str: the output of the command.

    """
    proc = subprocess.run(
        shlex.split(cmd, posix=False),
        shell=False,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    output = proc.stdout.decode("utf-8")
    if outfile:
        Path(outfile).write_text(output)

    return proc.returncode == 0, output.strip()

def canonical_url(url: str) -> str:
    """Canonicalize a repo URL, probably on GitHub."""
    for pat, repl in [
        (r"^git\+", ""),
        (r"#.$", ""),
        (r"\.git$", ""),
        (r"^git:", "https:"),
        (r"^ssh://git@", "https://"),
        (r"^git@github.com:", "https://github.com/"),
    ]:
        url = re.sub(pat, repl, url)
    if ":" not in url and url.count("/") == 1:
        url = f"https://github.com/{url}"
    return url

WORK_DIR = Path("/tmp/unpack_reqs")

def parallel_map(func, data, description):
    """Run func over data using threads, with a progress bar."""
    data = list(data)
    n_workers = os.cpu_count() or 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        with Progress(*Progress.get_default_columns(), MofNCompleteColumn()) as progress:
            pbar = progress.add_task(f"{description:20}", total=len(data))
            for result in executor.map(func, data):
                progress.update(pbar, advance=1)
                yield result

SOURCE_URL_REGEXES = [
    # These regexes are tried in order. The first group is the extracted URL.
    r"(?i)^Project-URL: Source.*,\s*(.*)$",
    r"(?i)^Home-page: (.*)$",
    r"(?i)^Project-URL: Home.*,\s*(.*)$",
    # If they point to GitHub issues, that's their repo.
    r"(?i)^Project-URL: [^,]+,\s*(https?://github.com/[^/]+/[^/]+)/issues/?$",
    # If we can't find a URL marked as home, then use any GitHub repo URL.
    r"(?i)^Project-URL: [^,]+,\s*(https?://github.com/[^/]+/[^/]+)$",
]

def repo_url_from_metadata(filename, metadata):
    """Find the likely source repo URL from PyPI metadata."""
    repo_url = matching_text(metadata, SOURCE_URL_REGEXES)
    if repo_url is None:
        print(f"No repo URL in {filename}")
        return None
    if repo_url == "UNKNOWN":
        print(f"Repo URL is UNKNOWN in {filename}")
        return None
    return repo_url

# The first of these we find is the requirements file we'll examine:
PY_REQS = [
    # "requirements/edx/base.txt",
    #"requirements/edx/base.in",
    "requirements/edx/kernel.in",
    #"requirements/edx/bundled.in",
    #"requirements/edx/testing.in",
    # "requirements/base.txt",
    #"requirements/base.in",
    "requirements/kernel.in",
    # "requirements.txt",
]

# Files that indicate a repo is a Python project:
PY_INDICATORS = [
    "setup.py",
    "setup.cfg",
    "pyproject.toml",
]

def find_py_reqs():
    """Find the Python requirements file to use."""
    for fname in PY_REQS:
        possible_req = Path(fname)
        if possible_req.exists():
            return possible_req
    if any(Path(ind).exists() for ind in PY_INDICATORS):
        print(f"WARNING: {os.getcwd()} is likely a Python package, but we can't find its dependencies.")
    return None

def request_package_info_url(package):
        base_url = "https://pypi.org/pypi/"
        url = f"{base_url}{package}/json"
        response = requests.get(url)
        if response.status_code == 200:
            data_dict = response.json()
            info = data_dict["info"]
            home_page = info["home_page"]
            return home_page
        else:
            print(f"Failed to retrieve data for package {package}. Status code:", response.status_code)    

def find_file_in_project(filename):
    """
    Recursively searches for a file within the project directory.

    Args:
    - filename: The name of the file to search for.

    Returns:
    - A list of file paths where the file was found.
    """
    # Get the current working directory
    project_root = os.getcwd()

    # List to store paths of found files
    found_paths = []

    # Recursively search for the file in the project directory
    for root, dirs, files in os.walk(project_root):
        if filename in files:
            # Construct the full path of the found file
            file_path = os.path.join(root, filename)
            found_paths.append(file_path)

    return found_paths



def process_directory():
    """
    Find all the requirements in the current directory. Returns a set of repo URLs.

    Also copies the considered dependencies file into the temp work directory,
    for later analysis.
    """    
    repo_name = Path.cwd().name
    repo_work = WORK_DIR / repo_name
    repo_work.mkdir(parents=True, exist_ok=True)
    repo_urls = set()
    package_names = []
    openedx_packages = [] 
    if (js_reqs := Path("package-lock.json")).exists():
        shutil.copyfile(js_reqs, repo_work / "package-lock.json")

    if (py_reqs := find_py_reqs()):
        shutil.copyfile(py_reqs, repo_work / "base.txt")

        with open(repo_work / "base.txt") as fbase:
            # Read each line (package name) in the file
            # with open('requirements.txt', 'r') as fd:
            for req in requirements.parse(fbase):
                print(req.name)
                home_page = request_package_info_url(req.name)
                if home_page is not None:
                    if match := urls_in_orgs([home_page], SECOND_PARTY_ORGS):
                        openedx_packages.append(home_page)

    return openedx_packages

FIRST_PARTY_ORGS = ["openedx"]

SECOND_PARTY_ORGS = [
    "edx", "edx-unsupported", "edx-solutions",
    "mitodl",
    "overhangio",
    "open-craft", "eduNEXT", "raccoongang",
]

def urls_in_orgs(urls, orgs):
    """
    Find urls that are in any of the `orgs`.
    """
    return sorted(
        url for url in urls
        if any(f"/{org}/" in url for org in orgs)
    )


def main(dirs=None, org=None):
    """
    Analyze the requirements in all of the directories mentioned on the command line.
    If arguments have newlines, treat each line as a separate directory.
    """
    repo_urls = set()
    repo_urls.update(process_directory())

    print("== DONE ==============")
    print("Second-party:")
    print("\n".join(repo_urls))
    if repo_urls:
        sys.exit(1)

if __name__ == "__main__":
    main()
