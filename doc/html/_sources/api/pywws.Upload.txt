pywws.Upload
============

Introduction
------------

This module uploads files to (typically) a website *via* ftp/sftp or copies files to a local directory (e.g. if you are running pywws on the your web server). Details of the upload destination are stored in the file ``weather.ini`` in your data directory. The only way to set these details is to edit the file. Run Upload.py once to set the default values, which you can then change. Here is what you're likely to find when you edit ``weather.ini``::

  [ftp]
  secure = False
  directory = public_html/weather/data/
  local site = False
  password = secret
  site = ftp.username.your_isp.co.uk
  user = username

These are, I hope, fairly obvious. The ``local site`` option lets you switch from uploading to a remote site to copying to a local site. If you set ``local site = True`` then you can delete the ``secure``, ``site``, ``user`` and ``password`` lines.

``directory`` is the name of a directory in which all the uploaded files will be put. This will depend on the structure of your web site and the sort of host you use. Your hosting provider should be able to tell you what ``site`` and ``user`` details to use. You should have already chosen a ``password``.

The ``secure`` option lets you switch from normal ftp to sftp (ftp over ssh). Some hosting providers offer this as a more secure upload mechanism, so you should probably use it if available.

Detailed API
------------

.. automodule:: pywws.Upload
   
   .. rubric:: Functions

   .. autosummary::
   
      Upload
      main
