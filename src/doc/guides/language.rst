.. pywws - Python software for USB Wireless Weather Stations
   http://github.com/jim-easterbrook/pywws
   Copyright (C) 2008-14  Jim Easterbrook  jim@jim-easterbrook.me.uk

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

Using an existing language file
-------------------------------

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
Now you can edit the language entry in your ``weather.ini`` file to use your language code.

If the above test shows no translations into your language then you need to create a new language file, as described below.

Dependencies
------------

As well as the pywws software you need to install the Babel python library (see :ref:`dependencies <dependencies-translations>`).
This is used to convert the language file you create into code that is used when the pywws software is run.
You also need to download and extract the pywws software instead of installing it with pip.
See :doc:`getstarted`.

.. _using-transifex:

Translating the easy way - the Transifex web site
-------------------------------------------------

`Transifex <https://www.transifex.com/>`_ is a web based system for coordinating teams of translators.
It is free to use for open source projects such as pywws.
In May 2014 I created a `pywws project <https://www.transifex.com/projects/p/pywws/>`_ on Transifex.
If you'd like to use Transifex to help translate pywws, please create an account (it's free) and join the appropriate language team.

Visit the pywws project page on Transifex and click on your language, then click on the "resource" you want to translate.
(``pywws`` contains the program strings used when running pywws, the others contain strings from the pywws documentation.)
This opens a dialog where you can choose to download a file to work on or translate the strings online.
Please read :ref:`translator-notes` before you start.

When you've finished translating ``pywws`` select the "download for use" option and save the file to ``src/pywws/lang/fr/LC_MESSAGES/pywws.po`` (replace ``fr`` with your language code).
Now you can :ref:`test-translation`.

.. versionadded:: 14.05.dev1221
   pywws now includes a config file for the ``transifex-client`` program (see :ref:`dependencies <dependencies-translations>`).
   This simplifies the process of downloading files for testing (or uploading files you've been editing on your computer).

For example, this command downloads any updated files for the French language::
   
   tx pull -l fr

Translating the hard way - using local files
--------------------------------------------

If you prefer not to use the Transifex web site you can edit language files on your own computer.
This is done in several stages, as follows.

Extract source strings
^^^^^^^^^^^^^^^^^^^^^^

Program messages are marked in the Python source with an underscore character.
These strings are extracted using setup.py::

   mkdir -p build/gettext
   python setup.py extract_messages

This creates the file ``build/gettext/pywws.pot``.
This is a "portable object template" file that contains the English language strings to be translated.

Create language files
^^^^^^^^^^^^^^^^^^^^^

The .pot files have headers that need to be initialised.
This can be done manually, but the Babel library has an ``init_catalog`` command to simplify the process::

   python setup.py init_catalog --locale fr

If a .po file for your language already exists, but needs updating with new source strings, you should use the ``update_catalog`` command instead::

   python setup.py update_catalog --locale fr

Now you can open the ``src/pywws/lang/fr/LC_MESSAGES/pywws.po`` file in your favourite text editor and start filling in the empty ``msgstr`` strings with your translation of the corresponding ``msgid`` string.
Please read :ref:`translator-notes` before you start.

.. _test-translation:

Test the pywws translation
--------------------------

After you've edited your language file it needs to be compiled so that pywws can use it.
This is done with setup.py::

   python setup.py compile_catalog --locale fr

After compilation you can test the translation::

   python setup.py build
   sudo python setup.py install
   python -m pywws.Localisation -t fr

Don't forget to do this every time you edit a language file.

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
Otherwise, please email me any .po files you create.
Please include details of which version of pywws your work is based on -- the easiest way to do this is to include the value of ``_commit`` from the file ``src/pywws/__init__.py`` in your email.

Translating the documentation
-----------------------------

The Sphinx program used to compile the pywws documentation has good support for translation into other languages, but the process is a bit complicated.
I recommend reading `this overview <http://sphinx-doc.org/latest/intl.html>`_, but don't follow its instructions.
I've tried to simplify the process, as described below.

As before, the easiest way to contribute to the pywws documentation translations is via the Transifex web site (see :ref:`using-transifex`).
You don't need to translate everything -- even a partial translation could be useful.
Just let me know when you've done enough to be worth publishing.

If you prefer not to use Transifex then please follow these instructions.

Extract source strings
^^^^^^^^^^^^^^^^^^^^^^

Documentation strings are extracted using setup.py::

   python setup.py extract_messages_doc

This creates several .pot files in the ``build/gettext/`` directory.

Create language files
^^^^^^^^^^^^^^^^^^^^^

The sphinx-intl command is used to create or update the .po files::

   sphinx-intl update --locale-dir src/pywws/lang -p build/gettext -l fr

Viewing your translated documentation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

First delete the old documentation (if it exists) and then rebuild using your language::

   rm -rf doc/fr
   LANG=fr python setup.py build_sphinx

Note that the ``build_sphinx`` command doesn't have a ``--locale`` (or ``-l``) option, so the language is set by a temporary environment variable.

Finally you can view the translated documentation by using a web browser to read the file ``doc/fr/html/index.html``.

As before, please make sure you send your translation to jim@jim-easterbrook.me.uk so other pywws users can benefit from your work.