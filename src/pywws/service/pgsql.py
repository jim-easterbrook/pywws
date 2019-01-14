"""pgsql.py: pywws service module for sending weather data to PgSQL DB"""
__author__ = "Michael Koelbl <mkoelbl@koelbl-it.de>"
__copyright__ = "Copyright 2019, Michael Kölbl"
__license__ = "BSD"
__version__ = "1.0.0"


"""Upload data to a PostgreSQL database.

weather.ini
    [pgsql]
    host = PGSQL host (fully qualified domain name or IP)
    username = PGSQL user
    password = PGSQL secret
    database = PGSQL database name
    table = Table name within database

    [logged]
    services = ['pgsql']

    [live]
    services = ['pgsql']


To use you have to create the table for storing the weather values within your
PGSQL database. The following example calls this table 'weather' but you can
use any table name you want. The fields must not be renamed.

PGSQL command to create table:

CREATE TABLE 'weather' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
'ts' INTEGER NOT NULL,
'realtime' BOOL NOT NULL,
'delay' INTEGER NOT NULL,
'abs_pressure' FLOAT NOT NULL,
'dewpoint_out' FLOAT NOT NULL,
'dewpoint_in' FLOAT NOT NULL,
'humidity_in' FLOAT NOT NULL,
'humidity_out' FLOAT NOT NULL,
'illuminance' FLOAT,
'rain' FLOAT NOT NULL,
'temp_in' FLOAT NOT NULL,
'temp_out' FLOAT NOT NULL,
'uv' FLOAT,
'wind_gust' FLOAT NOT NULL,
'wind_ave' FLOAT NOT NULL,
'wind_level' INTEGER NOT NULL,
'wind_dir_pos' INTEGER NOT NULL,
'wind_dir' VARCHAR(3) NOT NULL,
'forecast' VARCHAR(6) NOT NULL);

"""

from __future__ import absolute_import, unicode_literals
from ast import literal_eval
from contextlib import contextmanager
from datetime import datetime, timedelta
import logging
import os
import sys
import requests
import pywws.service
import psycopg2
import psycopg2.extras
import time as t
import math
from pywws.conversions import dew_point


__docformat__ = "restructuredtext en"
service_name = os.path.splitext(os.path.basename(__file__))[0]
logger = logging.getLogger(__name__)
RTFREQ = timedelta(seconds=48)


class DB():
    """Class for database handling"""
    def __init__(self, connstr):
        """Try connecting to PGSQL"""
        try:
            self.conn = psycopg2.connect(connstr)
            self.c = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        except:
            print 'ERROR:  Unable to connect to PostgreSQL'

    def query(self, query):
        """Send a query and return result"""
        self.c.execute(query)
        self.conn.commit()
        try:
            return self.c.fetchall()
        except psycopg2.ProgrammingError:
            return None

    def queryone(self, query):
        """Send query and expect one row"""
        self.c.execute(query)
        self.conn.commit()
        try:
            return self.c.fetchone()
        except psycopg2.ProgrammingError:
            return None

    def close(self):
        """Close connection to PGSQL"""
        self.conn.close()

    def __delete__(self):
        """Deconstructor"""
        self.close()


class ToService(pywws.service.CatchupDataService):
    config = {
        'host': ('', True, 'HOST'),
        'username': ('', True, 'USERNAME'),
        'password': ('', True, 'PASSWORD'),
        'database': ('', True, 'DATABASE NAME'),
        'table': ('', True, 'DATABASE TABLE'),
        }
    fixed_data = {'action': 'updateraw', 'softwaretype': 'pywws'}
    interval = timedelta(seconds=47)
    logger = logger
    service_name = service_name
    template = """
#live#
#idx          "'dateutc'     : '%Y-%m-%d %H:%M:%S',"#
#wind_dir     "'winddir'     : '%.0f'," "" "winddir_degrees(x)"#
#wind_ave     "'windspeedmph': '%.2f'," "" "wind_mph(x)"#
#wind_gust    "'windgustmph' : '%.2f'," "" "wind_mph(x)"#
#hum_out      "'humidity'    : '%.d',"#
#temp_out     "'tempf'       : '%.1f'," "" "temp_f(x)"#
#rel_pressure "'baromin'     : '%.4f'," "" "pressure_inhg(x)"#
#calc "temp_f(dew_point(data['temp_out'], data['hum_out']))" "'dewptf': '%.1f',"#
#calc "rain_inch(rain_hour(data))" "'rainin': '%g',"#
#calc "rain_inch(rain_day(data))" "'dailyrainin': '%g',"#
#hum_in       "'indoorhumidity': '%.d',"#
#temp_in      "'indoortempf'   : '%.1f'," "" "temp_f(x)"#
"""

    def __init__(self, context, check_params=True):
        super(ToService, self).__init__(context, check_params)
        self.wstype = 1080
        # extend template
        if context.params.get('config', 'ws type') == '3080':
            self.wstype = 3080
            self.template += """
#illuminance  "'solarradiation': '%.2f'," "" "illuminance_wm2(x)"#
#uv           "'UV'            : '%d',"#
"""

    @contextmanager
    def session(self):
        yield None

    def fahrenheit2celsius(self, fahrenheit):
        """Convert fahrenheit to celsius"""
        return (float(fahrenheit) - 32) * 5.0 / 9.0

    def mph2kmh(self, mph):
        """Convert mph to km/h"""
        return float(mph) / 0.62137119

    def winddir_text(self, pts):
        """Convert wind direction value to text"""
        if pts == None: return 'N'
        if not isinstance(pts, int):
            pts = int(pts + 0.5) % 16
        winddir = [
        'N', 'NNE', 'NE', 'ENE',
        'E', 'ESE', 'SE', 'SSE',
        'S', 'SSW', 'SW', 'WSW',
        'W', 'WNW', 'NW', 'NNW'
        ]
        return winddir[pts]

    def wind_level_bft(self, wind_mph):
        """Convert wind speed (mph) to wind level (bft)"""
        map_wl = []
        map_wl.append([0,0.999])
        map_wl.append([1,5])
        map_wl.append([6,11])
        map_wl.append([12,19])
        map_wl.append([20,28])
        map_wl.append([29,38])
        map_wl.append([39,49])
        map_wl.append([50,61])
        map_wl.append([62,74])
        map_wl.append([75,88])
        map_wl.append([89,102])
        map_wl.append([103,117])
        map_wl.append([117,999])
        wind = self.mph2kmh(float(wind_mph))
        for i in range(0, 12):
            if wind >= map_wl[i][0] and wind <= map_wl[i][1]:
                return i

    def dewpoint_c(self, tempf, humidity):
        """Calculate dewpoint and return celsius value"""
        return self.fahrenheit2celsius(dew_point(float(tempf),
                                       float(humidity)))

    def inhg2hpa(self, inhg):
        """Convert InHG to hPa"""
        return float(inhg) / 0.029529983071455

    def hpa2height(self, hpa):
        """Return height in meters based on pressure"""
        return (1013.25 - float(hpa)) * 8

    def forecast(self, inhg):
        """Forecast weather based on barometric pressure"""
        hpa = self.inhg2hpa(float(inhg))
        if hpa < 980:
            return 'STORMY'
        elif hpa >= 980 and hpa < 1000:
            return 'RAINY'
        elif hpa >= 1000 and hpa < 1020:
            return 'NORMAL'
        elif hpa >= 1021 and hpa <= 1040:
            return 'SUNNY'
        elif hpa > 1040:
            return 'DRY'

    def upload_data(self, session, prepared_data={}):
        # extract timestamp from prepared_data
        idx = datetime.strptime(prepared_data['dateutc'], '%Y-%m-%d %H:%M:%S')
        if datetime.utcnow() - idx < RTFREQ:
            prepared_data.update({'realtime': '1', 'rtfreq': '48'})
        else:
            prepared_data.update({'realtime': '0', 'rtfreq': '48'})
        try:
            db = DB("host='%s' dbname='%s' user='%s' password='%s'" %
                    (self.params['host'], self.params['database'],
                     self.params['username'], self.params['password']))
            if self.wstype != 3080:
                prepared_data['UV'] = '-1'
                prepared_data['solarradiation'] = '-1'
            query = "INSERT INTO %s (ts,realtime,delay,abs_pressure," \
                    "dewpoint_out,dewpoint_in,humidity_in,humidity_out," \
                    "illuminance,rain,temp_in,temp_out,uv,wind_gust," \
                    "wind_ave,wind_level,wind_dir_pos,wind_dir,forecast) " \
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s," \
                    "%s,%s,%s,'%s','%s');" % \
                    (str(self.params['table']),
                    str(int(t.time())),
                    str(prepared_data['realtime']),
                    str(prepared_data['rtfreq']),
                    str(self.inhg2hpa(prepared_data['baromin'])),
                    str(self.fahrenheit2celsius(prepared_data['dewptf'])),
                    str(self.dewpoint_c(prepared_data['indoortempf'],
                                        prepared_data['indoorhumidity'])),
                    str(prepared_data['indoorhumidity']),
                    str(prepared_data['humidity']),
                    str(prepared_data['solarradiation']),
                    str(prepared_data['rainin']),
                    str(self.fahrenheit2celsius(prepared_data['indoortempf'])),
                    str(self.fahrenheit2celsius(prepared_data['tempf'])),
                    str(prepared_data['UV']),
                    str(self.mph2kmh(prepared_data['windgustmph'])),
                    str(self.mph2kmh(prepared_data['windspeedmph'])),
                    str(self.wind_level(prepared_data['windspeedmph'])),
                    str(prepared_data['winddir']),
                    str(self.winddir_text(float(prepared_data['winddir']))),
                    str(self.forecast(float(prepared_data['baromin']))))
            db.query(query)
            db.close()

        except Exception as ex:
            logger.warning("PGSQL: Upload exception %s", ex)
            return False, repr(ex)
        return True, 'OK'


if __name__ == "__main__":
    sys.exit(pywws.service.main(ToService))

