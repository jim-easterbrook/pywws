"""Localisation.py - provide translations of strings into local language"""

import gettext
import locale
import os
import sys

def SetLanguage(params=None):
    global trans
    #Check the default locale
    lc, encoding = locale.getdefaultlocale()
    # make list of possible languages, in order of preference
    langs = []
    if params:
        lang = params.get('config', 'language', lc)
        if lang:
            langs += [lang, lang[:2]]
    if lc:
        langs += [lc, lc[:2]]
    # Add one we know to be there
    langs += ["en_GB", "en"]
    # set translation object
    trans = gettext.translation(
        'pywws', os.path.join(os.path.dirname(sys.argv[0]), 'locale'),
        languages=langs)
    trans.install()
def Charset():
    global trans
    charset = trans._charset
    if charset in (None, 'ASCII'):
        charset = 'iso-8859-1'
    return charset
SetLanguage()