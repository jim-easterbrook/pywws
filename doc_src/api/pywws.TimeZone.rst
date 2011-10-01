pywws.TimeZone
==============

Introduction
------------

This module provides two ``datetime.tzinfo`` objects representing UTC and local time zones. These are used to convert timestamps to and from UTC and local time. The weather station software stores data with UTC timestamps, to avoid problems with daylight savings time, but the template and plot programs output data with local times.

The module is copied directly from the ``datetime.tzinfo`` module documentation.

Detailed API
------------

.. automodule:: pywws.TimeZone

   .. rubric:: Classes

   .. autosummary::
   
      LocalTimezone
      UTC
