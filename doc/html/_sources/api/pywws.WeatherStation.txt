pywws.WeatherStation
====================

Introduction
------------

This is the module that actually talks to the weather station base unit. I don't have much understanding of USB, so copied a lot from Michael Pendec's C program wwsr.

The weather station memory has two parts: a "fixed block" of 256 bytes and a circular buffer of 65280 bytes. As each weather reading takes 16 bytes the station can store 4080 readings, or 14 days of 5-minute interval readings. As data is read in 32-byte chunks, but each weather reading is 16 bytes, a small cache is used to reduce USB traffic. The caching behaviour can be over-ridden with the ``unbuffered`` parameter to ``get_data`` and ``get_raw_data``.

Decoding the data is controlled by the static dictionaries ``reading_format``, ``lo_fix_format`` and ``fixed_format``. The keys are names of data items and the values can be an ``(offset, type and multiplier)`` tuple or another dictionary. So, for example, the reading_format dictionary entry ``'rain' : (13, 'us', 0.3)`` means that the rain value is an unsigned short (two bytes), 13 bytes from the start of the block, and should be multiplied by 0.3 to get a useful value.

The use of nested dictionaries in the ``fixed_format`` dictionary allows useful subsets of data to be decoded. For example, to decode the entire block ``get_fixed_block`` is called with no parameters::

  ws = WeatherStation.weather_station()
  print ws.get_fixed_block()

To get the stored minimum external temperature, ``get_fixed_block`` is called with a sequence of keys::

  ws = WeatherStation.weather_station()
  print ws.get_fixed_block(['min', 'temp_out', 'val'])

Often there is no requirement to read and decode the entire fixed block, as its first 64 bytes contain the most useful data: the interval between stored readings, the buffer address where the current reading is stored, and the current date & time. The ``get_lo_fix_block`` method provides easy access to these.

For more examples of using the WeatherStation module, see the TestWeatherStation program.

Detailed API
------------

.. automodule:: pywws.WeatherStation
   
   .. rubric:: Functions

   .. autosummary::
   
      apparent_temp
      dew_point
      findDevice
      get_wind_dir_text
      pressure_trend_text
      set_translation
      wind_chill
   
   .. rubric:: Classes

   .. autosummary::
   
      CUSBDrive
      weather_station
