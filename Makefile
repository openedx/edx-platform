# Do things in edx-platform

clean:
	# Remove all the git-ignored stuff, but save and restore things marked
	# by start-noclean/end-noclean.
	sed -n -e '/start-noclean/,/end-noclean/p' < .gitignore > /tmp/private-files
	tar cf /tmp/private.tar `git ls-files --exclude-from=/tmp/private-files --ignored --others`
	git clean -fdX
	tar xf /tmp/private.tar
