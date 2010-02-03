"""Localisation.py - provide translations of strings into local language"""

import gettext
import locale
import os

langs = []
#Check the default locale
lc, encoding = locale.getdefaultlocale()
if lc:
    langs = [lc]
# Next get all of the supported languages on the system
language = os.environ.get('LANG', None)
if language:
	langs += map(lambda x: x.split('.')[0], language.split(":"))
# Finally, add one we know to be there
langs += ["en_GB"]
trans = gettext.translation('pywws', './locale', languages=langs)
_ = trans.lgettext
