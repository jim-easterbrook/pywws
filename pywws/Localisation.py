#!/usr/bin/env python

"""Localisation.py - provide translations of strings into local
language
::

%s

Localisation of pywws is done in two parts - translating strings such
as 'rising very rapidly', and changing the 'locale' which controls
things like month names and number representation ('23,2' instead of
'23.2').

"""

__docformat__ = "restructuredtext en"

__usage__ = """
 usage: python pywws/Localisation.py [options]
 options are:
  -h       or  --help       display this help
  -t code  or  --test code  test use of a language code
"""

__doc__ %= __usage__
__usage__ = __doc__.split('\n')[0] + __usage__

import getopt
import gettext
import locale
import os
import sys
import time

# set translation to be used if SetTranslation is not called
translation = gettext.NullTranslations()

def SetLocale(lang):
    # get the default locale
    lc, encoding = locale.getdefaultlocale()
    try:
        if '.' in lang:
            locale.setlocale(locale.LC_ALL, lang)
        else:
            locale.setlocale(locale.LC_ALL, (lang, encoding))
    except locale.Error:
        return False
    return True

def SetTranslation(lang):
    global translation
    # make list of possible languages, in order of preference
    langs = list()
    if lang:
        if '.' in lang:
            lang = lang.split('.')[0]
        langs += [lang, lang[:2]]
    # get translation object
    path = os.path.join(os.path.dirname(sys.argv[0]), '..', 'locale')
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(sys.argv[0]), 'locale')
    try:
        translation = gettext.translation('pywws', path, languages=langs)
    except IOError:
        return False
    return True

def SetApplicationLanguage(params):
    lang = params.get('config', 'language', None)
    if lang:
        SetLocale(lang)
        SetTranslation(lang)

def main(argv=None):
    if argv is None:
        argv = sys.argv
    try:
        opts, args = getopt.getopt(argv[1:], "ht:", ['help', 'test='])
    except getopt.error, msg:
        print >>sys.stderr, 'Error: %s\n' % msg
        print >>sys.stderr, __usage__.strip()
        return 1
    # process options
    code = None
    for o, a in opts:
        if o in ('-h', '--help'):
            print __usage__.strip()
            return 0
        elif o in ('-t', '--test'):
            code = a
    # check arguments
    if len(args) != 0:
        print >>sys.stderr, 'Error: no arguments required\n'
        print >>sys.stderr, __usage__.strip()
        return 2
    # test language code
    if code:
        old_locale = locale.getlocale()
        if SetLocale(code):
            new_locale = locale.getlocale()
            print "Locale changed from", old_locale, "to", new_locale
        else:
            print "Failed to set locale:", code
        if SetTranslation(code):
            print "Translation set OK"
        else:
            print "No translation file found for:", code
    # try a few locale / translation effects
    print "Locale"
    print "  decimal point:", locale.format("%4.1f", 23.2)
    print "  date & time:", time.strftime("%A, %d %B (%x %X)")
    print "Translations"
    print "  'NNW' => '%s'" % (translation.lgettext('NNW'))
    print "  'rising very rapidly' => '%s'" % (
        translation.lgettext('rising very rapidly'))
    print "  'Rain at times, very unsettled' => '%s'" % (
        translation.lgettext('Rain at times, very unsettled'))
    return 0

if __name__ == "__main__":
    sys.exit(main())
