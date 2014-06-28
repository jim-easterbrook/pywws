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

Humidity Index (Humidex)
========================

.. sectionauthor:: Rodney Persky

Background
----------

Using your weather station can be fun, and reporting daily to various weather data sites can be very useful for your neighbours to check out the weather. However, at some point you may want to know how the weather effects your body, and if there is a way to tell when it's good or not to work outdoors.

Here enters a whole realm of calculations based on energy transferring though walls, and the resistance offered by them. It can be a great learning adventure, and can save you a great deal of money, finding out how energy moves around.

Introduction
------------

Humidex is a tool to determine how an individuals body will react to the combination of Wind, Humidity and Temperature. The background of which is a heat balance across from your midriff to your skin, and is complimentary to ISO 7243 "Hot Environments - Estimation of the heat stress on working man". A few important notes,

* These indices are based off a number of assumptions which may result in over or under-estimation of your bodies internal state
* A personal weather station may not show the correct conditions, and may have an over or under estimation of the humidity, wind or temperature
* Clothing choices effect the personal fatigue and the bodies ability to reject heat, a low Humidity Index doesn't mean you can wear anything
* An individuals fitness will effect their bodies response to changing temperature, and experience will aid in knowing when to stop working
* The duration of activities that can be performed requires knowledge on the intensity, which cannot be represented though this index


Assumptions
-----------

There are a number of assumptions that have been made to make this work which will directly affect its useability. These assumptions however have not been made available from Environment Canada, who are the original developers of the Humidex used in the PYWWS function cadhumidex. It is safe enough however to say that the following would have been some assumptions:

* Clothing type, thickness
* Skin area exposed to free air
* Sun exposure

However, there are a number of assumptions pywws needs to make in calculating the Humidex:

* The humidity, wind and temperature readings are correct

There are also assumptions about the individuals body type and 'acclimatisation'

* An individuals fitness will effect their bodies response to changing temperature
* Experience will aid in knowing when to stop working

Important References
--------------------

Being Prepared for Summer - http://www.ec.gc.ca/meteo-weather/default.asp?lang=En&n=86C0425B-1

How to use
----------

The function is descriptively named ``cadhumidex`` and has the parameters temperature and humidity, essentially the function operates as a conversion and can be used in a straightforward manner::

<ycalc>cadhumidex(data['temp_out'],data['hum_out'])</ycalc>

Putting it together, I have added colours that follow basic warning colors and the different brackets to produce a decent graph::

  <?xml version="1.0" encoding="ISO-8859-1"?>
  <graph>
    <title>Humidity Index, Bands indicate apparent discomfort in standard on-site working conditions</title>
    <size>1820, 1024</size>
    <duration>hours=48</duration>
    <xtics>2</xtics>
    <xformat>%H%M</xformat>
    <dateformat></dateformat>
    <plot>
      <yrange>29, 55</yrange>
      <y2range>29, 55</y2range>
      <ylabel></ylabel>
      <y2label>Humidex</y2label>
      <source>raw</source>
      <subplot>
        <title>Humidex</title>
        <ycalc>cadhumidex(data['temp_out'],data['hum_out'])</ycalc>
        <colour>4</colour>
        <axes>x1y2</axes>
      </subplot>
      <subplot>
        <title>HI > 54, Heat Stroke Probable</title>
        <ycalc>54</ycalc>
        <axes>x1y2</axes>
        <colour>1</colour>
      </subplot>
      <subplot>
        <title>HI > 45, Dangerous</title>
        <ycalc>45</ycalc>
        <axes>x1y2</axes>
        <colour>8</colour>
      </subplot>
      <subplot>
        <title>HI > 40, Intense</title>
        <ycalc>40</ycalc>
        <axes>x1y2</axes>
        <colour>6</colour>
      </subplot>
      <subplot>
        <title>HI > 35, Evident</title>
        <ycalc>35</ycalc>
        <axes>x1y2</axes>
        <colour>2</colour>
      </subplot>
      <subplot>
        <title>HI > 30, Noticeable</title>
        <ycalc>30</ycalc>
        <axes>x1y2</axes>
        <colour>3</colour>
      </subplot>
    </plot>
  </graph>

Not running the latest update?
------------------------------

If you are not running the latest update / do not want to, then this can be implemented using a longer <ycalc> as follows::

<ycalc>data['temp_out']+0.555*(6.112*10**(7.5*data['temp_out']/(237.7+data['temp_out']))*data['hum_out']/100-10)</ycalc>
