pywws.ToTwitter
===============

Introduction
------------

This module posts a brief message to `Twitter <https://twitter.com/>`_. Account details are stored in the file ``weather.ini`` in your data directory. The only way to set these details is to edit the file. Run ToTwitter.py once to set the default values, which you can then change. Here is what you're likely to find when you edit weather.ini. ::

  [twitter]
  username = twitterusername
  password = twitterpassword

The example template ``tweet.txt`` can be used to create your message. Note that the message will be truncated to 140 characters if it is too long.

Detailed API
------------

.. automodule:: pywws.ToTwitter
   
   .. rubric:: Functions

   .. autosummary::
   
      main
   
   .. rubric:: Classes

   .. autosummary::
   
      ToTwitter
