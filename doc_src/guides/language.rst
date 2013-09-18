.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-13  Jim Easterbrook  jim@jim-easterbrook.me.uk

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

How to use pywws in another language
====================================

Introduction
------------

Some parts of pywws can be configured to use your local language instead of British English.
This requires an appropriate language file which contains translations of the various strings used in pywws.
The pywws project relies on users to provide these translations.
This document describes how to create a language file.

The pywws documentation can also be translated into other languages.
This is a lot more work, but could be very useful to potential users who do not read English very well.

Dependencies
------------

As well as the pywws software you need to install the ``gettext`` GNU internationalisation utilities package.
This is available from the standard repositories for most Linux distributions, or you can download it from http://www.gnu.org/software/gettext/ if you need to compile it yourself.

Choose your language code
-------------------------

Computers use IETF language tags (see http://en.wikipedia.org/wiki/IETF_language_tag).
For example, in the UK we use ``en_GB``.
This has two parts: ``en`` for English, and ``GB`` for the British version of it.
To find the correct code for your language, consult the list at http://www.gnu.org/software/gettext/manual/gettext.html#Language-Codes.

Getting started
---------------

Your pywws directory should already have a subdirectory called translations.
This contains the existing set of language files, for example ``translations/sv/pywws.po`` contains the Swedish translations.
If one of these languages is what you need, then edit your weather.ini file and add a ``language`` entry to the ``[config]`` section, for example::

   [config]
   day end hour = 21
   gnuplot encoding = iso_8859_1
   language = sv

You may still need to compile and install your chosen language file.
This is done with ``setup.py``::

   python setup.py msgfmt

If there isn't already a file for your language, the rest of this document tells you how to create one.

Create a language file
----------------------

The first step is to create a file containing the strings you need to translate.
For example, to create a source file for the French language (code ``fr``)::

   python setup.py xgettext
   python setup.py msgmerge --lang=fr

This will ask you to confirm your email address, then create a ``pywws.po`` file in the directory ``translations/fr``.
You should now edit ``pywws.po``, filling in every ``msgstr`` line with a translation of the ``msgid`` line immediately above it.
The reason for including your email address is to allow anyone who has questions about your translation to get in touch with you.
Feel free to put in an invalid address if you are concerned about privacy.

After you've edited your new language file it needs to be compiled so that pywws can use it.
This is done with the ``msgfmt`` command::

   python setup.py msgfmt

Don't forget to do this every time you edit a language file.

Test the pywws translation
--------------------------

The :py:mod:`~pywws.Localisation` module can be used to do a quick test of your language file installation::

   python -m pywws.Localisation -t fr

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

Edit the language entry in your ``weather.ini`` file to use your language code (e.g. ``fr``), then try using :py:mod:`~pywws.Plot` to plot a graph.
The X-axis of the graph should now be labeled in your language, using the translation you provided for 'Time', 'Day' or 'Date'.

Translating the documentation
-----------------------------

The system used to translate the strings used in pywws can also be used to translate the documentation.
The command to extract strings from the documentation is very similar::

   python setup.py xgettext_doc

Note that this requires the `sphinx <http://sphinx-doc.org/>`_ package used to 'compile' the documentation.
After extracting the strings, create source files for your language.
In this example the language is French, with the two letter code ``fr``::
   
   python setup.py msgmerge --lang=fr

This creates four files (``index.po``, ``essential.po``, ``guides.po`` and ``api.po``) that contain text strings (often whole paragraphs) extracted from the different parts of the documentation.

These files can be edited in a similar way to ``pywws.po``.
Fill in each ``msgstr`` with a translation of the ``msgid`` above it.
Note that some strings (such as URLs and links to other parts of the documentation) should not be translated.
In these cases, leave the ``msgstr`` blank.

Translating all of the pywws documentation is a lot of work.
However, when the documentation is 'compiled' any untranslated strings revert to their English original.
This means that a partial translation could still be useful -- I suggest starting with the documentation front page, ``index.po``.

Viewing your translated documentation
-------------------------------------

First convert your newly edited language files::

   python setup.py msgfmt

Then delete the old documentation (if it exists) and rebuild using your language::

   rm -Rf doc/html/fr
   LANG=fr python setup.py build_sphinx

Note that the ``build_sphinx`` command doesn't have a ``--lang`` option, so the language is set by a temporary environment variable.

Finally you can view the translated documentation by using a web browser to read the file ``doc/html/fr/index.html``.

Update the language files
-------------------------

As pywws is extended, new strings may be added which will require your translation files to be extended as well.
This is fairly easy to do.
First you need to re-extract the strings to be translated, then merge them into your existing language files.
This is done by repeating the commands used to create the files::

   python setup.py xgettext
   python setup.py xgettext_doc
   python setup.py msgmerge --lang=fr

This should add the new strings to your language files, without changing the strings you've already translated.

If the English language source has changed since your last translation, some strings may be marked by gettext as ``#, fuzzy``.
You should check that your translation is still correct for these strings -- the change may be trivial (e.g. a spelling correction) but it could be quite significant.
When you've checked (and corrected if necessary) the translation, remove the ``#, fuzzy`` line.

Send Jim the translation
------------------------

I'm sure you would like others to benefit from the work you've done in translating pywws.
Please, please, please send a copy of your language file(s) (for example ``pywws.po``) to jim@jim-easterbrook.me.uk.
When you send a new translation you need to include details of which pywws version it is based on -- the easiest way to do this is to include the value of ``commit`` from the file ``pywws/version.py`` in your email.

Comments or questions? Please subscribe to the pywws mailing list http://groups.google.com/group/pywws and let us know.