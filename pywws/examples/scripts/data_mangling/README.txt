Data mangling scripts
=====================

These scripts must be used with extremem caution! They are provided as starting
points for any data modifications you need to do as a result of some unusual
event that has affected your data. In all cases, make sure you do the following:

1/ Copy one of the example scripts and edit it to do what you need.
2/ Stop all pywws software, and any cron job that might restart it.
3/ Backup your weather data.
4/ Check that you really have backed up your data.
5/ Run the script.
6/ Check the results, carefully.
7/ If all is well, restart pywws.

rain_offset.py
--------------

This script subtracts a fixed value from all the rain data in a given range of
time stamps. This could be useful if you had an unusual event such as the wind
resonating with the rain gauge and tipping the see-saw multiple times. Removing
the batteries from the external sensors will reset the rain count, but your data
will still have an unwanted jump which a script like this can remove.

temperature_despike.py
----------------------

This uses a median filter to remove spikes in the external temperature data,
possibly caused by electrical interference. It substitutes a 'missing data'
value, rather than attempt to interpolate from adjacent values.