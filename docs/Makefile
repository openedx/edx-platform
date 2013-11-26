
.PHONY: html

Q_FLAG =

ifeq ($(quiet), true)
Q_FLAG = quiet=true
endif

html:
	@cd $(CURDIR)/data && make html $(Q_FLAG)
	@cd $(CURDIR)/course_authors && make html $(Q_FLAG)
	@cd $(CURDIR)/developers && make html $(Q_FLAG)
