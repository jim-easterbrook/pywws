lang_src	:= $(wildcard languages/*.po)

ifdef LANG
  LC	:= $(firstword $(subst ., ,$(LANG)))
else
  LC	:= en
endif

all : doc lang pywws/version.py README.txt

.PHONY : doc clean

doc :
	cd doc_src && $(MAKE) html text

clean :
	find doc -name "*.html" -delete
	find doc -name "*.txt" -delete
	rm -f doc/html/.buildinfo doc/html/objects.inv doc/html/searchindex.js
	rm -Rf doc/doctrees

README.txt : doc/text/essentials/README.txt
	cp -p $< $@
	
lang : \
	languages/$(LC).po \
	$(lang_src:languages/%.po=locale/%/LC_MESSAGES/pywws.mo)

# create a version file
.PHONY : pywws/version.py
REVISION	:= $(shell svn info 2>/dev/null | awk '/^Revision/ {print $$2}')
ifneq '$(REVISION)' ''
  pywws/version.py :
	date +"version = '%y.%m_r$(REVISION)'" >$@
endif

# compile a language file
locale/%/LC_MESSAGES/pywws.mo : languages/%.po
	mkdir -p $(dir $@)
	msgfmt --output-file=$@ $<

# create or update a language file from extracted strings
languages/$(LC).po : languages/pywws.pot
	if [ -e $@ ]; then \
	  cd $(dir $<) ; \
	  msgmerge $(notdir $@ $<) --update ; \
	else \
	  msginit --input=$< --output=- --locale=$(LC) | \
	  sed 's/PACKAGE/pywws/' | sed 's/ VERSION//' >$@ ; \
	fi

# extract marked strings from Python files
languages/pywws.pot :
	xgettext --language=Python --output=- \
		--copyright-holder="Jim Easterbrook" \
		--msgid-bugs-address="jim@jim-easterbrook.me.uk" \
		*.py pywws/*.py | \
	sed 's/PACKAGE VERSION/pywws/' >$@
