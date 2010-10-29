html_src	:= $(wildcard doc/html/*)
lang_src	:= $(wildcard languages/*.po)

all : doc lang

doc : \
	$(html_src:doc/html/%.html=doc/txt/%.txt)
	
lang : \
	$(lang_src:languages/%.po=locale/%/LC_MESSAGES/pywws.mo)

doc/txt/%.txt : doc/html/%.html
	links -dump -width 80 $< >$@

locale/%/LC_MESSAGES/pywws.mo : languages/%.po
	mkdir -p $(dir $@)
	msgfmt --output-file=$@ $<
