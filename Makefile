# Do things in edx-platform
.PHONY: clean extract_translations help pull pull_translations push_translations requirements shell upgrade
.PHONY: api-docs docs guides swagger

# Careful with mktemp syntax: it has to work on Mac and Ubuntu, which have differences.
PRIVATE_FILES := $(shell mktemp -u /tmp/private_files.XXXXXX)

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## archive and delete most git-ignored files
	@# Remove all the git-ignored stuff, but save and restore things marked
	@# by start-noclean/end-noclean. Include Makefile in the tarball so that
	@# there's always at least one file even if there are no private files.
	sed -n -e '/start-noclean/,/end-noclean/p' < .gitignore > /tmp/private-files
	-tar cf $(PRIVATE_FILES) Makefile `git ls-files --exclude-from=/tmp/private-files --ignored --others`
	-git clean -fdX
	tar xf $(PRIVATE_FILES)
	rm $(PRIVATE_FILES)

SWAGGER = docs/swagger.yaml

docs: api-docs guides technical-docs ## build all the developer documentation for this repository

swagger: ## generate the swagger.yaml file
	DJANGO_SETTINGS_MODULE=docs.docs_settings python manage.py lms generate_swagger --generator-class=edx_api_doc_tools.ApiSchemaGenerator -o $(SWAGGER)

api-docs-sphinx: swagger	## generate the sphinx source files for api-docs
	rm -f docs/api/gen/*
	python docs/sw2sphinxopenapi.py $(SWAGGER) docs/api/gen

api-docs: api-docs-sphinx	## build the REST api docs
	cd docs/api; make html

technical-docs:  ## build the technical docs
	$(MAKE) -C docs/technical html

guides:	## build the developer guide docs
	cd docs/guides; make clean html

extract_translations: ## extract localizable strings from sources
	i18n_tool extract -v

push_translations: ## push source strings to Transifex for translation
	i18n_tool transifex push

pull_translations:  ## pull translations from Transifex
	git clean -fdX conf/locale
	i18n_tool transifex pull
	i18n_tool extract
	i18n_tool dummy
	i18n_tool generate --verbose 1
	git clean -fdX conf/locale/rtl
	git clean -fdX conf/locale/eo
	i18n_tool validate --verbose
	paver i18n_compilejs


detect_changed_source_translations: ## check if translation files are up-to-date
	i18n_tool changed

pull: ## update the Docker image used by "make shell"
	docker pull edxops/edxapp:latest

pre-requirements: ## install Python requirements for running pip-tools
	pip install -r requirements/pip.txt
	pip install -r requirements/pip-tools.txt

local-requirements:
# 	edx-platform installs some Python projects from within the edx-platform repo itself.
	pip install -e .

dev-requirements: pre-requirements
	@# The "$(wildcard..)" is to include private.txt if it exists, and make no mention
	@# of it if it does not.  Shell wildcarding can't do that with default options.
	pip-sync requirements/edx/development.txt $(wildcard requirements/edx/private.txt)
	make local-requirements

base-requirements: pre-requirements
	pip-sync requirements/edx/base.txt
	make local-requirements

test-requirements: pre-requirements
	pip-sync --pip-args="--exists-action=w" requirements/edx/testing.txt
	make local-requirements

requirements: dev-requirements ## install development environment requirements

shell: ## launch a bash shell in a Docker container with all edx-platform dependencies installed
	docker run -it -e "NO_PYTHON_UNINSTALL=1" -e "PIP_INDEX_URL=https://pypi.python.org/simple" -e TERM \
	-v `pwd`:/edx/app/edxapp/edx-platform:cached \
	-v edxapp_lms_assets:/edx/var/edxapp/staticfiles/ \
	-v edxapp_node_modules:/edx/app/edxapp/edx-platform/node_modules \
	edxops/edxapp:latest /edx/app/edxapp/devstack.sh open

# Order is very important in this list: files must appear after everything they include!
REQ_FILES = \
	requirements/edx/coverage \
	requirements/edx/doc \
	requirements/edx/paver \
	requirements/edx-sandbox/py38 \
	requirements/edx/base \
	requirements/edx/testing \
	requirements/edx/development \
	scripts/xblock/requirements

define COMMON_CONSTRAINTS_TEMP_COMMENT
# This is a temporary solution to override the real common_constraints.txt\n# In edx-lint, until the pyjwt constraint in edx-lint has been removed.\n# See BOM-2721 for more details.\n# Below is the copied and edited version of common_constraints\n
endef

COMMON_CONSTRAINTS_TXT=requirements/common_constraints.txt
.PHONY: $(COMMON_CONSTRAINTS_TXT)
$(COMMON_CONSTRAINTS_TXT):
	wget -O "$(@)" https://raw.githubusercontent.com/edx/edx-lint/master/edx_lint/files/common_constraints.txt || touch "$(@)"
	echo "$(COMMON_CONSTRAINTS_TEMP_COMMENT)" | cat - $(@) > temp && mv temp $(@)

compile-requirements: export CUSTOM_COMPILE_COMMAND=make upgrade
compile-requirements: pre-requirements $(COMMON_CONSTRAINTS_TXT) ## Re-compile *.in requirements to *.txt
	@# Bootstrapping: Rebuild pip and pip-tools first, and then install them
	@# so that if there are any failures we'll know now, rather than the next
	@# time someone tries to use the outputs.
	pip-compile -v --allow-unsafe ${COMPILE_OPTS} -o requirements/pip.txt requirements/pip.in
	pip install -r requirements/pip.txt

	pip-compile -v ${COMPILE_OPTS} -o requirements/pip-tools.txt requirements/pip-tools.in
	pip install -r requirements/pip-tools.txt

	@ export REBUILD='--rebuild'; \
	for f in $(REQ_FILES); do \
		echo ; \
		echo "== $$f ===============================" ; \
		echo "pip-compile -v $$REBUILD ${COMPILE_OPTS} -o $$f.txt $$f.in"; \
		pip-compile -v $$REBUILD ${COMPILE_OPTS} -o $$f.txt $$f.in || exit 1; \
		export REBUILD=''; \
	done

upgrade:  ## update the pip requirements files to use the latest releases satisfying our constraints
	$(MAKE) compile-requirements COMPILE_OPTS="--upgrade"

check-types: ## run static type-checking tests
	mypy

docker_build:
	DOCKER_BUILDKIT=1 docker build . --build-arg SERVICE_VARIANT=lms --build-arg SERVICE_PORT=8000 --target development -t openedx/lms-dev
	DOCKER_BUILDKIT=1 docker build . --build-arg SERVICE_VARIANT=lms --build-arg SERVICE_PORT=8000 --target production -t openedx/lms
	DOCKER_BUILDKIT=1 docker build . --build-arg SERVICE_VARIANT=cms --build-arg SERVICE_PORT=8010 --target development -t openedx/cms-dev
	DOCKER_BUILDKIT=1 docker build . --build-arg SERVICE_VARIANT=cms --build-arg SERVICE_PORT=8010 --target production -t openedx/cms

docker_tag: docker_build
	docker tag openedx/lms     openedx/lms:${GITHUB_SHA}
	docker tag openedx/lms-dev openedx/lms-dev:${GITHUB_SHA}
	docker tag openedx/cms     openedx/cms:${GITHUB_SHA}
	docker tag openedx/cms-dev openedx/cms-dev:${GITHUB_SHA}

docker_auth:
	echo "$$DOCKERHUB_PASSWORD" | docker login -u "$$DOCKERHUB_USERNAME" --password-stdin

docker_push: docker_tag docker_auth ## push to docker hub
	docker push "openedx/lms:latest"
	docker push "openedx/lms:${GITHUB_SHA}"
	docker push "openedx/lms-dev:latest"
	docker push "openedx/lms-dev:${GITHUB_SHA}"
	docker push "openedx/cms:latest"
	docker push "openedx/cms:${GITHUB_SHA}"
	docker push "openedx/cms-dev:latest"
	docker push "openedx/cms-dev:${GITHUB_SHA}"

lint-imports:
	lint-imports

# WARNING (EXPERIMENTAL):
# This installs the Ubuntu requirements necessary to make `pip install` and some other basic
# dev commands to pass. This is not necessarily everything needed to get a working edx-platform.
# Part of https://github.com/openedx/wg-developer-experience/issues/136
ubuntu-requirements: ## Install ubuntu 22.04 system packages needed for `pip install` to work on ubuntu.
	sudo apt install libmysqlclient-dev libxmlsec1-dev
