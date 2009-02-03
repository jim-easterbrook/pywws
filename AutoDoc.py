#!/usr/bin/env python

from HTMLParser import HTMLParser
import os
import pydoc
import sys
from urlparse import urlparse

class CorrectLinks(HTMLParser):
    def process(self, in_file, out_file, name):
        self.reset()
        self._out = out_file
        self._name = name
        self._subst = None
        self.feed(in_file.read())
        self.close()
    def handle_starttag(self, tag, attrs, startend=False):
        if tag == 'a':
            for idx in range(len(attrs)):
                key, value = attrs[idx]
                if key != 'href':
                    continue
                if value == '.':
                    attrs[idx] = ('href', '../index.html')
                elif 'http:' in value:
                    # external link - don't change
                    pass
                else:
                    url = urlparse(value)
                    if url.scheme == 'file':
                        # probably a link to full path of Python module
                        # convert to relative path, and change text link as well
                        self._subst = os.path.basename(url.path)
                        if self._subst.lower() == self._name.lower():
                            attrs[idx] = ('href', '../../%s' % self._name)
                        else:
                            self._subst = None
                    else:
                        base, ext = os.path.splitext(url.path)
                        if ext == '.html' and not os.path.exists(base + '.py'):
                            # most likely a standard Python module
                            attrs[idx] = (
                                'href',
                                'http://docs.python.org/library/%s' % value.lower())
        self._out.write('<%s' % tag)
        for key, value in attrs:
            self._out.write(' %s="%s"' % (key, value))
        if startend:
            self._out.write(' />')
        else:
            self._out.write('>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, True)
    def handle_endtag(self, tag):
        self._subst = None
        self._out.write('</%s>' % tag)
    def handle_data(self, data):
        if self._subst:
            data = self._name
        self._out.write(data)
    def handle_charref(self, name):
        raise Exception("unhandled charref")
    def handle_entityref(self, name):
        self._out.write('&%s;' % name)
    def handle_comment(self, name):
        raise Exception("unhandled comment")
    def handle_decl(self, decl):
        self._out.write('<!%s>' % decl)
    def handle_pi(self, data):
        raise Exception("unhandled pi")
def AutoDoc():
    doc_dir = 'doc/auto'
    if not os.path.isdir(doc_dir):
        os.mkdir(doc_dir)
    wd = os.getcwd()
    link_corrector = CorrectLinks()
    for file in os.listdir('./'):
        base, ext = os.path.splitext(file)
        if ext != '.py':
            continue
        pydoc.writedoc(base)
        src_file = base + '.html'
        if not os.path.exists(src_file):
            continue
        # post-process pydoc output to clean up some of its eccentricities
        dest_file = os.path.join(doc_dir, src_file)
        src = open(src_file, 'r')
        dest = open(dest_file, 'w')
        link_corrector.process(src, dest, file)
        dest.close()
        src.close()
        os.unlink(src_file)
    return 0
if __name__ == "__main__":
    sys.exit(AutoDoc())
