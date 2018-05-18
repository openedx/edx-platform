# Do things in edx-platform
.PHONY: clean extract_translations help pull_translations push_translations requirements upgrade

# Careful with mktemp syntax: it has to work on Mac and Ubuntu, which have differences.
PRIVATE_FILES := $(shell mktemp -u /tmp/private_files.XXXXXX)

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## archive and delete most git-ignored files
	# Remove all the git-ignored stuff, but save and restore things marked
	# by start-noclean/end-noclean. Include Makefile in the tarball so that
	# there's always at least one file even if there are no private files.
	sed -n -e '/start-noclean/,/end-noclean/p' < .gitignore > /tmp/private-files
	-tar cf $(PRIVATE_FILES) Makefile `git ls-files --exclude-from=/tmp/private-files --ignored --others`
	-git clean -fdX
	tar xf $(PRIVATE_FILES)
	rm $(PRIVATE_FILES)

extract_translations: ## extract localizable strings from sources
	i18n_tool extract -vv

push_translations: ## push source strings to Transifex for translation
	i18n_tool transifex push

pull_translations: ## pull translations from Transifex
	git clean -fdX conf/locale
	i18n_tool transifex pull
	i18n_tool extract
	i18n_tool dummy
	i18n_tool generate
	i18n_tool generate --strict
	git clean -fdX conf/locale/rtl
	git clean -fdX conf/locale/eo
	i18n_tool validate

requirements: ## install development environment requirements
	pip install -qr requirements/edx/development.txt --exists-action w

upgrade: ## update the pip requirements files to use the latest releases satisfying our constraints
	pip install -qr requirements/edx/pip-tools.txt
	# Make sure to compile files after any other files they include!
	pip-compile --upgrade -o requirements/edx/pip-tools.txt requirements/edx/pip-tools.in
	pip-compile --upgrade -o requirements/edx/coverage.txt requirements/edx/coverage.in
	pip-compile --upgrade -o requirements/edx/paver.txt requirements/edx/paver.in
	pip-compile --upgrade -o requirements/edx-sandbox/shared.txt requirements/edx-sandbox/shared.in
	pip-compile --upgrade -o requirements/edx-sandbox/base.txt requirements/edx-sandbox/base.in
	pip-compile --upgrade -o requirements/edx/base.txt requirements/edx/base.in
	pip-compile --upgrade -o requirements/edx/testing.txt requirements/edx/testing.in
	pip-compile --upgrade -o requirements/edx/development.txt requirements/edx/development.in
	# Post process all of the files generated above to work around open pip-tools issues
	scripts/post-pip-compile.sh \
        requirements/edx/pip-tools.txt \
	    requirements/edx/coverage.txt \
	    requirements/edx/paver.txt \
	    requirements/edx-sandbox/shared.txt \
	    requirements/edx-sandbox/base.txt \
	    requirements/edx/base.txt \
	    requirements/edx/testing.txt \
	    requirements/edx/development.txt
	# Let tox control the Django version for tests
	grep "^django==" requirements/edx/base.txt > requirements/edx/django.txt
	sed '/^[dD]jango==/d' requirements/edx/testing.txt > requirements/edx/testing.tmp
	mv requirements/edx/testing.tmp requirements/edx/testing.txt
