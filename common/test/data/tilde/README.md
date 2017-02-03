DO NOT DELETE TILDE FILES

This course simulates an export that has been edited by hand, where the editor's
text editor has left behind some backup files (about/index.html~ and
static/example.txt~). Normally, we do not commit files that end with tildes to
the repository, for precisely this reason -- they are backup files, and do
not belong with the content. However, in this case, we *need* these backup files
to be committed to the repository, so that we can exercise logic in the codebase
that checks for these sort of editor backup files and skips them on export.
