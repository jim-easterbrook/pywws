#!/usr/bin/env python

from HTMLParser import HTMLParser
import os
import pydoc
import sys
from urlparse import urlparse

class CorrectLinks(HTMLParser):
    def process(self, in_file, out_file):
        self.reset()
        self._out = out_file
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
                        attrs[idx] = (
                            'href', url.path.replace(self.path_old, self.path_new))
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
            data = self._subst
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
    os.chdir(os.path.dirname(sys.argv[0]))
    doc_dir = 'doc/html/auto'
    link_corrector = CorrectLinks()
    link_corrector.path_old = os.getcwd()
    link_corrector.path_new = '../../..'
    def PostProcess(module):
        # post-process pydoc output to clean up some of its eccentricities
        # and move to doc_dir
        src_file = module + '.html'
        if not os.path.exists(src_file):
            return
        dest_file = os.path.join(doc_dir, src_file)
        src = open(src_file, 'r')
        dest = open(dest_file, 'w')
        link_corrector.process(src, dest)
        dest.close()
        src.close()
        os.unlink(src_file)
    if not os.path.isdir(doc_dir):
        os.mkdir(doc_dir)
##    for module in ['math', 'usb', 'datetime', 'getopt', 'sys', 'csv', 'os',
##                   'time', 'shlex', 'ftplib', 'shutil', 're', 'codecs',
##                   'twitter', 'pydoc']:
##        pydoc.writedoc(module)
##        PostProcess(module)
    for file in os.listdir('.'):
        base, ext = os.path.splitext(file)
        if ext != '.py':
            continue
        if base in ('setup'):
            continue
        pydoc.writedoc(base)
        PostProcess(base)
    for file in os.listdir('pywws'):
        base, ext = os.path.splitext(file)
        if ext != '.py':
            continue
        if base in ('__init__'):
            continue
        base = 'pywws.%s' % base
        pydoc.writedoc(base)
        PostProcess(base)
    return 0
if __name__ == "__main__":
    sys.exit(AutoDoc())
