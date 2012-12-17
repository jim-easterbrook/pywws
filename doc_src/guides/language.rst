How to use pywws in another language
====================================

#. Introduction.

   Some parts of pywws can be configured to use your local language instead
   of British English. This requires an appropriate language file which
   contains translations of the various strings used in pywws. The pywws
   project relies on users to provide these translations. This document
   describes how to create a language file.

   The pywws documentation can also be translated into other languages. This is a lot more work, but could be very useful to potential users who do not read English very well.

#. Dependencies.

   As well as the pywws software you need to install the 'gettext' GNU
   internationalisation utilities package. This is available from the
   standard repositories for most Linux distributions, or you can download it
   from http://www.gnu.org/software/gettext/ if you need to compile it
   yourself.

#. Choose your language code.

   Computers use IETF language tags (see
   http://en.wikipedia.org/wiki/IETF_language_tag). For example, in the UK we
   use 'en_GB'. This has two parts: 'en' for English, and 'GB' for the
   British version of it. To find the correct code for your language, consult
   the list at
   http://www.gnu.org/software/gettext/manual/gettext.html#Language-Codes.

#. Getting started.

   Your pywws directory should already have a subdirectory called translations.
   This contains the existing set of language files, for example 'translations/sv/pywws.po'
   contains the Swedish translations. If one of these languages is what you
   need, then edit your weather.ini file and add a 'language' entry to the
   '[config]' section, for example::

      [config]
      day end hour = 21
      gnuplot encoding = iso_8859_1
      language = sv

   You may still need to compile and install your chosen language file. This is done by the 'makefile' included with pywws::

      make lang LANG=sv

   If there isn't already a file for your language, the rest of this document
   tells you how to create one.

#. Create a language file.

   The 'makefile' included with pywws can create a file for you to
   fill in. For example, to create a source file for the French language (code 'fr')::

      make lang_src LANG=fr

   This will ask you to confirm your email address (several times, annoyingly), then create several '.po' files in the directory 'translations/fr'. You should now edit 'pywws.po', filling in every 'msgstr' line with a translation of the 'msgid' line immediately above it. The reason for including your email address is to allow anyone who has questions about your translation to get in touch with you. Feel free to put in an invalid address if you are concerned about privacy.

   After you've edited your new language file it needs to be compiled so that
   pywws can use it. This is also done by the makefile::

      make lang LANG=fr

   Don't forget to do this every time you edit a language file.

#. Test the pywws translation.

   The Localisation.py module can be used to do a quick test of your language file installation::

      python code/RunModule.py Localisation -t fr

   This should produce output something like this::

      Locale changed from (None, None) to ('fr_FR', 'UTF-8')
      Translation set OK
      Locale
        decimal point: 23,2
        date & time: lundi, 17 décembre (17/12/2012 16:00:48)
      Translations
        'NNW' => 'NNO'
        'rising very rapidly' => 'en hausse très rapide'
        'Rain at times, very unsettled' => 'Quelques précipitations, très perturbé'

   Edit the language entry in your weather.ini file to use your language code
   (e.g. 'fr'), then try using Plot.py to plot a graph. The X-axis of the
   graph should now be labeled in your language, using the translation you
   provided for 'Time', 'Day' or 'Date'.

#. Send Jim the language file.

   I'm sure you would like others to benefit from the work you've done in
   making a new language file for pywws. Please, please, please send a copy
   of your language file (for example pywws.po) to jim@jim-easterbrook.me.uk.

#. Update the language file.

   As pywws is extended, new strings may be added which will require your
   translation file to be extended as well. This is fairly easy to do. First
   you need to remove the language master template file, then run the 'make lang_src' command again::

      rm translations/pywws.pot
      make lang_src LANG=fr

   This should add the
   new strings to your language file, without changing the strings you've
   already translated.

#. Translating the documentation.

   The system used to translate the strings used in pywws can also be used to translate the documentation. The files 'index.po', 'essential.po', 'guides.po' and 'api.po' contain text strings (often whole paragraphs) extracted from the different parts of the documentation.

   These files can be edited in a similar way to 'pywws.po'. Fill in each 'msgstr' with a translation of the 'msgid' above it. Note that some strings (such as URLs) need not be translated. In these cases, leave the 'msgstr' blank.

   Translating all of the pywws documentation is a lot of work. However, when the documentation is 'compiled' any untranslated strings revert to their English original. This means that a partial translation could still be useful - I suggest starting with the documentation front page, 'index.po'.

   Comments or questions? Please subscribe to the pywws mailing list
   http://groups.google.com/group/pywws and let us know.