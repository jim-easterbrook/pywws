How to make a language file for pywws
=====================================

#. Introduction.

   Some parts of pywws can be configured to use your local language instead
   of British English. This requires an appropriate language file which
   contains translations of the various strings used in pywws. The pywws
   project relies on users to provide these translations. This document
   describes how to create a language file.

#. Dependencies.

   As well as the pywws software you need to install the 'gettext' GNU
   internationalisation utilities package. This is available from the
   standard repositories for most Linux distributions, or you can download it
   from http://www.gnu.org/software/gettext/ if you need to compile it
   yourself.

#. Getting started.

   Your pywws directory should already have a subdirectory called languages.
   This contains the existing set of language files, for example 'sv.po'
   contains the Swedish translations. If one of these languages is what you
   need, then edit your weather.ini file and add a 'language' entry to the
   '[config]' section, for example::

      [config]
      day end hour = 21
      gnuplot encoding = iso_8859_1
      language = sv

   If there isn't already a file for your language, the rest of this document
   tells you how to create one.

#. Choose your language code.

   Computers use IETF language tags (see
   http://en.wikipedia.org/wiki/IETF_language_tag). For example, in the UK we
   use 'en_GB'. This has two parts: 'en' for English, and 'GB' for the
   British version of it. To find the correct code for your language, consult
   the list at
   http://www.gnu.org/software/gettext/manual/gettext.html#Language-Codes.

#. Create a language file.

   The 'makefile' included with pywws can create a template file for you to
   fill in. For example, to create a file for the French language (code 'fr')::

      make code/languages/fr.po

   This will ask you to confirm your email address, then create a file 'code/languages/fr.po'. You should now edit this file, filling in every 'msgstr' line with a translation of the 'msgid' line immediately above it. The reason for including your email address is to allow anyone who has questions about your translation to get in touch with you. Feel free to put in an invalid address if you are concerned about privacy.

   After you've edited your new language file it needs to be compiled so that
   pywws can use it. This is also done by the makefile::

      make lang

   Don't forget to do this every time you edit a language file.

#. Test the pywws translation.

   Edit the language entry in your weather.ini file to use your language code
   (e.g. 'fr'), then try using Plot.py to plot a graph. The X-axis of the
   graph should now be labeled in your language, using the translation you
   provided for 'Time', 'Day' or 'Date'.

#. Send Jim the language file.

   I'm sure you would like others to benefit from the work you've done in
   making a new language file for pywws. Please, please, please send a copy
   of your language file (for example fr.po) to jim@jim-easterbrook.me.uk.

#. Update the language file.

   As pywws is extended, new strings may be added which will require your
   translation file to be extended as well. This is fairly easy to do. First
   you need to remove the language master template file::

      rm code/languages/pywws.pot

   Now run the make command again as in section 5 above. This should add the
   new strings to your language file, without changing the strings you've
   already translated.

   Comments or questions? Please subscribe to the pywws mailing list
   http://groups.google.com/group/pywws and let us know.