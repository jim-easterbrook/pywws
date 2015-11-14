.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-15  pywws contributors

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

The pywws documentation can also be translated into other languages.
This is a lot more work, but could be very useful to potential users who do not read English very well.

Using existing language files
-----------------------------

Program strings
^^^^^^^^^^^^^^^

There may already be a pywws translation for your preferred language.
First you need to choose the appropriate two-letter code from the list at http://www.w3schools.com/tags/ref_language_codes.asp.
For example, ``fr`` is the code for French.
Now use the :py:mod:`pywws.Localisation` module to do a quick test::

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

This shows that pywws is already able to generate French output, and that your installation is correctly configured.
Now you can edit the ``language`` entry in your :ref:`weather.ini <weather_ini-config>` file to use your language code.

If the above test shows no translations into your language then you need to create a new language file, as described below.

Text encodings
^^^^^^^^^^^^^^

The pywws default text encoding is ISO-8859-1, also known as Latin-1.
This is suitable for several western European languages but not for some others.
If you encounter problems you may need to use a different encoding.
See the documentation of :py:mod:`pywws.Template` and :py:mod:`pywws.Plot` for more details.

Documentation
^^^^^^^^^^^^^

If you have downloaded the pywws source files, or cloned the GitHub repository (see :ref:`how to get started with pywws <getstarted-download>`), you can compile a non-English copy of the documentation.
This requires the `Sphinx <http://sphinx-doc.org/>`_ package, see :ref:`dependencies <dependencies-compile-documentation>`.

First delete the old documentation (if it exists) and then recompile using your language::

   cd ~/weather/pywws
   rm -rf doc
   LANG=fr python setup.py build_sphinx

Note that the ``build_sphinx`` command doesn't have a ``--locale`` (or ``-l``) option, so the language is set by a temporary environment variable.

You can view the translated documentation by using a web browser to read the file ``~/weather/pywws/doc/html/index.html``.

Writing new language files
--------------------------

There are two ways to write new language files (or update existing ones) -- use the `Transifex <https://www.transifex.com/>`_ online system or use local files.
Transifex is preferred as it allows several people to work on the same language, and makes your work instantly available to others.

To test your translation you will need to have downloaded the pywws source files, or cloned the GitHub repository (see :ref:`how to get started with pywws <getstarted-download>`).
You will also need to install the ``Babel`` package, see :ref:`dependencies <dependencies-translations>`.

.. _using-transifex:

Using Transifex
^^^^^^^^^^^^^^^

If you'd like to use Transifex, please go to the `pywws Transifex project <https://www.transifex.com/projects/p/pywws/>`_, click on "help translate pywws" and create a free account.

Visit the pywws project page on Transifex and click on your language, then click on the "resource" you want to translate.
(``pywws`` contains the program strings used when running pywws, the others contain strings from the pywws documentation.)
This opens a dialog where you can choose to translate the strings online.
Please read :ref:`translator-notes` before you start.

When you have finished translating you should use the ``transifex-client`` program (see :ref:`dependencies <dependencies-translations>`) to download files for testing.
For example, this command downloads any updated files for the French language::
   
   cd ~/weather/pywws
   tx pull -l fr

Now you are ready to :ref:`test-translation`.

Using local files
^^^^^^^^^^^^^^^^^

If you prefer not to use the Transifex web site you can edit language files on your own computer.
This is done in two stages, as follows.

Extract source strings
""""""""""""""""""""""

Program messages are extracted using the ``Babel`` package::

   cd ~/weather/pywws
   mkdir -p build/gettext
   python setup.py extract_messages

This creates the file ``build/gettext/pywws.pot``.
This is a "portable object template" file that contains the English language strings to be translated.

The documentation strings are extracted using the ``Sphinx`` package::

   cd ~/weather/pywws
   python setup.py extract_messages_doc

This creates several ``.pot`` files in the ``build/gettext/`` directory.

Create language files
"""""""""""""""""""""

The ``sphinx-intl`` command is used to convert the ``.pot`` files to language specific ``.po`` files::

   cd ~/weather/pywws
   sphinx-intl update --locale-dir src/pywws/lang -p build/gettext -l fr

Now you can open the ``.po`` files in ``src/pywws/lang/fr/LC_MESSAGES/`` with your favourite text editor and start filling in the empty ``msgstr`` strings with your translation of the corresponding ``msgid`` string.
Please read :ref:`translator-notes` before you start.

.. _test-translation:

Test the pywws translations
---------------------------

The ``Babel`` package is used to compile program strings::

   python setup.py compile_catalog --locale fr

(Replace ``fr`` with the code for the language you are testing.)

After compilation you can test the translation::

   python setup.py build
   sudo python setup.py install
   python -m pywws.Localisation -t fr

``Sphinx`` is used to build the translated documentation::

   cd ~/weather/pywws
   rm -rf doc
   LANG=fr python setup.py build_sphinx

You can view the translated documentation by using a web browser to read the file ``~/weather/pywws/doc/html/index.html``.

.. _translator-notes:

Notes for translators
---------------------

The pywws program strings (``pywws.po``) are quite simple.
They comprise simple weather forecasts ("Fine weather"), air pressure changes ("rising quickly") and the 16 points of the compass ("NNE").
Leave the "(%Z)" in "Time (%Z)" unchanged and make sure your translation's punctuation matches the original.

The other files contain strings from the pywws documentation.
These are in `reStructuredText <http://docutils.sourceforge.net/rst.html>`_.
This is mostly plain text, but uses characters such as backquotes (\`), colons (\:) and asterisks (\*) for special purposes.
You need to take care to preserve this special punctuation.
Do not translate program source, computer instructions and cross-references like these::

   `pip <http://www.pip-installer.org/>`_
   :py:class:`datetime.datetime`
   :obj:`ParamStore <pywws.DataStore.ParamStore>`\\ (root_dir, file_name)
   pywws.Forecast
   ``pywws-livelog``

Translating all of the pywws documentation is a lot of work.
However, when the documentation is "compiled" any untranslated strings revert to their English original.
This means that a partial translation could still be useful -- I suggest starting with the documentation front page, ``index.po``.

Send Jim the translation
------------------------

I'm sure you would like others to benefit from the work you've done in translating pywws.
If you've been using Transifex then please send me an email (jim@jim-easterbrook.me.uk) to let me know there's a new translation available.
Otherwise, please email me any ``.po`` files you create.
