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
	i18n_tool extract -v

push_translations: ## push source strings to Transifex for translation
	i18n_tool transifex push

pull_translations: ## pull translations from Transifex
	git clean -fdX conf/locale
	i18n_tool transifex pull
	i18n_tool extract
	i18n_tool dummy
	i18n_tool generate
	git clean -fdX conf/locale/rtl
	git clean -fdX conf/locale/eo
	i18n_tool validate

detect_changed_source_translations: ## check if translation files are up-to-date
	i18n_tool changed

requirements: ## install development environment requirements
	pip install -qr requirements/edx/development.txt --exists-action w

# Order is very important in this list: files must appear after everything they include!
REQ_FILES = \
	requirements/edx/pip-tools \
	requirements/edx/coverage \
	requirements/edx/paver \
	requirements/edx-sandbox/shared \
	requirements/edx-sandbox/base \
	requirements/edx/base \
	requirements/edx/testing \
	requirements/edx/development

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the pip requirements files to use the latest releases satisfying our constraints
	pip install -qr requirements/edx/pip-tools.txt
	@for f in $(REQ_FILES); do \
		echo ; \
		echo "== $$f ===============================" ; \
		pip-compile -v --no-emit-trusted-host --no-index --upgrade -o $$f.txt $$f.in || exit 1; \
	done
	# Post process all of the files generated above to work around open pip-tools issues
	scripts/post-pip-compile.sh $(REQ_FILES:=.txt)
	# Let tox control the Django version for tests
	grep "^django==" requirements/edx/base.txt > requirements/edx/django.txt
	sed '/^[dD]jango==/d' requirements/edx/testing.txt > requirements/edx/testing.tmp
	mv requirements/edx/testing.tmp requirements/edx/testing.txt
