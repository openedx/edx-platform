# Do things in edx-platform

# Careful with mktemp syntax: it has to work on Mac and Ubuntu, which have differences.
PRIVATE_FILES := $(shell mktemp -u /tmp/private_files.XXXXXX)

clean:
	# Remove all the git-ignored stuff, but save and restore things marked
	# by start-noclean/end-noclean. Include Makefile in the tarball so that
	# there's always at least one file even if there are no private files.
	sed -n -e '/start-noclean/,/end-noclean/p' < .gitignore > /tmp/private-files
	-tar cf $(PRIVATE_FILES) Makefile `git ls-files --exclude-from=/tmp/private-files --ignored --others`
	-git clean -fdX
	tar xf $(PRIVATE_FILES)
	rm $(PRIVATE_FILES)

extract_translations:
	# Extract localizable strings from sources
	i18n_tool extract -vv

push_translations:
	# Push source strings to Transifex for translation
	i18n_tool transifex push

pull_translations:
	## Pull translations from Transifex
	git clean -fdX conf/locale
	i18n_tool transifex pull
	i18n_tool extract
	i18n_tool dummy
	i18n_tool generate
	i18n_tool generate --strict
	git clean -fdX conf/locale/rtl
	git clean -fdX conf/locale/eo
	i18n_tool validate
