pywws.Localisation
==================

Introduction
------------

Some of the pywws modules, such as WindRose.py, can automatically use your local language for such things as wind directions. The Localisation.py module, mostly copied from examples in the Python documentation, enables this.

Before using pywws in your local language, you may need to write a translation file. Human languages have been given codes, such as 'en_GB' for British English or 'fr_CA' for Canadian French. To find out what language code you need, have a look at your computer's ``LANG`` environment variable with this command::

  echo $LANG

Now have a look in the 'languages' directory in your pywws installation. If there is a .po file whose name matches the first two characters of your ``LANG`` environment variable, then you don't need to do anything.

Creating a new translation
--------------------------

To create a new language file, first convert the supplied pywws.pot file to a template. For example, to create a French language template::

  make lang LANG=fr

This should create a suitable file, e.g. 'fr.po' in the 'languages' directory. Now edit the new .po file and translate all the 'msgstr' strings to your language.

Before the language file can be used, it needs to be converted to a machine readable form by running make again::

  make lang

When you are satisfied with your translation effort, please send me a copy of the .po file to add to the pywws distribution.

Using a different language
--------------------------

If you want pywws to use a different language to that specified by your ``LANG`` environment variable, you can specify it in your weather.ini file. Choose a language for which a translation exists, for example 'en', then add it to your weather.ini file as follows::

 [config]
 language = en

Detailed API
------------

.. automodule:: pywws.Localisation

   .. rubric:: Functions

   .. autosummary::
   
      GetTranslation   