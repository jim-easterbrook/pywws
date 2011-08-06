"""Localisation.py - provide translations of strings into local language"""

import gettext
import locale
import os
import sys

def GetTranslation(params):
    #Check the default locale
    lc, encoding = locale.getdefaultlocale()
    # make list of possible languages, in order of preference
    langs = []
    lang = params.get('config', 'language', lc)
    if lang:
        locale.setlocale(locale.LC_ALL, lang)
        langs += [lang, lang[:2]]
    if lc:
        langs += [lc, lc[:2]]
    # Add one we know to be there
    langs += ["en_GB", "en"]
    # get translation object
    try:
        return gettext.translation(
            'pywws', os.path.join(os.path.dirname(sys.argv[0]), '..', 'locale'),
            languages=langs)
    except IOError:
        return gettext.translation(
            'pywws', os.path.join(os.path.dirname(sys.argv[0]), 'locale'),
            languages=langs)
