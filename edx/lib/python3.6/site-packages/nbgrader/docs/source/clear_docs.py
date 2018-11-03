import os
import sys
import shutil
import subprocess as sp
from copy import deepcopy

try:
    from nbformat import read, write
    from nbconvert.preprocessors import ClearOutputPreprocessor
except ImportError:
    print("Warning: nbformat and/or nbconvert could not be imported, some tasks may not work")


def run(cmd):
    print(" ".join(cmd))
    proc = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.STDOUT)
    stdout, _ = proc.communicate()
    if proc.poll() != 0:
        print(stdout.decode())
        print("Command exited with code: {}".format(proc.poll()))
        sys.exit(1)


def _check_if_directory_in_path(pth, target):
    while pth not in ('', '/'):
        pth, dirname = os.path.split(pth)
        if dirname == target:
            return True
    return False


def clean_notebook_metadata(root):
    """Cleans the metadata of documentation notebooks."""

    print("Cleaning the metadata of notebooks in '{}'...".format(os.path.abspath(root)))

    for dirpath, dirnames, filenames in os.walk(root):
        is_submitted = _check_if_directory_in_path(dirpath, 'submitted')

        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with open(pth, 'r') as fh:
                    orig_nb = read(fh, 4)

                # copy the original notebook
                new_nb = clean_notebook(orig_nb)

                # write the notebook back to disk
                with open(pth, 'w') as fh:
                    write(new_nb, fh, 4)

                if orig_nb != new_nb:
                    print("Cleaned '{}'".format(pth))


def clear_notebooks(root):
    """Clear the outputs of documentation notebooks."""

    # cleanup ignored files
    run(['git', 'clean', '-fdX', root])

    # remove release/autograded/feedback
    if os.path.exists(os.path.join(root, "user_guide", "release")):
        shutil.rmtree(os.path.join(root, "user_guide", "release"))
    if os.path.exists(os.path.join(root, "user_guide", "autograded")):
        shutil.rmtree(os.path.join(root, "user_guide", "autograded"))
    if os.path.exists(os.path.join(root, "user_guide", "feedback")):
        shutil.rmtree(os.path.join(root, "user_guide", "feedback"))
    if os.path.exists(os.path.join(root, "user_guide", "downloaded", "ps1", "extracted")):
        shutil.rmtree(os.path.join(root, "user_guide", "downloaded", "ps1", "extracted"))

    print("Clearing outputs of notebooks in '{}'...".format(os.path.abspath(root)))
    preprocessor = ClearOutputPreprocessor()

    for dirpath, dirnames, filenames in os.walk(root):
        is_submitted = _check_if_directory_in_path(dirpath, 'submitted')

        for filename in sorted(filenames):
            if os.path.splitext(filename)[1] == '.ipynb':
                # read in the notebook
                pth = os.path.join(dirpath, filename)
                with open(pth, 'r') as fh:
                    orig_nb = read(fh, 4)

                # copy the original notebook
                new_nb = clean_notebook(orig_nb)

                # check outputs of all the cells
                if not is_submitted:
                    new_nb = preprocessor.preprocess(new_nb, {})[0]

                # write the notebook back to disk
                with open(pth, 'w') as fh:
                    write(new_nb, fh, 4)

                if orig_nb != new_nb:
                    print("Cleared '{}'".format(pth))


def clean_notebook(orig_nb):
    new_nb = deepcopy(orig_nb)
    clean_metadata(new_nb)
    return new_nb


def clean_metadata(new_nb):
    new_nb.metadata = {
        "kernelspec": {
            "display_name": "Python",
            "language": "python",
            "name": "python"
        }
    }


if __name__ == "__main__":
    root = os.path.abspath(os.path.dirname(__file__))
    clean_notebook_metadata(root)
