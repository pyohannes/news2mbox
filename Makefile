# +
#
DESTDIR=/usr/local/bin

all: news2mbox

fetzen = $(shell which fetzen 2>/dev/null)

ifneq ("$(wildcard $(fetzen))","")
    news2mbox: news2mbox_fetzen
else
    news2mbox: news2mbox_copy
endif

news2mbox_fetzen: python/news2mbox.py
	mkdir -p doc 
	"$(fetzen)" --preprocessor 'uncomment-#' --out doc/news2mbox.tex,docu-latex --out news2mbox,code $< 

news2mbox_copy: python/news2mbox.py
	cp $< news2mbox

news2mbox:
	chmod 755 $@

doc: news2mbox
	cd doc ; \
	pdflatex news2mbox.tex

clean:
	rm -rf doc news2mbox

install: news2mbox
	cp news2mbox ${DESTDIR}/
	chmod 755 ${DESTDIR}/news2mbox
