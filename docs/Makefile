# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help clean Makefile

clean:
	rm -rf _build cms common lms openedx

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

update_redirects:
	# This updates redirects.txt, creating redirects for any files that have moved (relative to master).
	sphinx-build -b rediraffewritediff "$(SOURCEDIR)" "$(BUILDDIR)"

check_redirects:
	# Check to make sure that any files that got moved have a redirect in redirects.txt
	sphinx-build -b rediraffecheckdiff "$(SOURCEDIR)" "$(BUILDDIR)"
