TestWeatherStation
==================

Introduction
------------

This is a simple utility to test communication with the weather station. If this doesn't work, then there's a problem that needs to be sorted out before trying any of the other programs. Likely problems include not properly installing `libusb <http://libusb.wiki.sourceforge.net/>`_ or `PyUSB <http://pyusb.berlios.de/>`_. Less likely problems include an incompatibility between libusb and some operating systems. The most unlikely problem is that you forgot to connect the weather station to your computer!

Detailed API
------------

.. automodule:: TestWeatherStation

   .. rubric:: Functions

   .. autosummary::
   
      main
      raw_dump