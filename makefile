all : doc lang code/pywws/version.py
	python setup.py build

install :
	python setup.py install

dist :
	python setup.py sdist

clean :
	rm -Rf doc/* code/pywws/locale/*

.PHONY : doc
doc : code/pywws/version.py
	$(MAKE) -C doc_src html text

lang_src	:= $(wildcard code/languages/*.po)
lang : $(lang_src:code/languages/%.po=code/pywws/locale/%/LC_MESSAGES/pywws.mo)

# create a version file
.PHONY : code/pywws/version.py
COMMIT	:= $(shell git rev-parse --short master)
code/pywws/version.py :
	date +"version = '%y.%m_$(COMMIT)'" >$@

# compile a language file
code/pywws/locale/%/LC_MESSAGES/pywws.mo : code/languages/%.po
	mkdir -p $(dir $@)
	msgfmt --output-file=$@ $<

# create or update a language file from extracted strings
code/languages/%.po : code/languages/pywws.pot
	if [ -e $@ ]; then \
	  cd $(dir $<) ; \
	  msgmerge $(notdir $@ $<) --update ; \
	  touch $(notdir $@) ; \
	else \
	  msginit --input=$< --output=- --locale=$* | \
	  sed 's/PACKAGE/pywws/' | sed 's/ VERSION//' >$@ ; \
	fi

# extract marked strings from Python files
code/languages/pywws.pot :
	xgettext --language=Python --output=- \
		--copyright-holder="Jim Easterbrook" \
		--msgid-bugs-address="jim@jim-easterbrook.me.uk" \
		code/*.py code/pywws/*.py | \
	sed 's/PACKAGE VERSION/pywws/' >$@
