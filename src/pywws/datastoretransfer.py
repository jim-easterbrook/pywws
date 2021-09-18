"""
This module transfers and converts the pywws weather station data from one
data format and directory to another.

Usage:
python -m pywws.datastoretransfer SOURCE_TYPE SOURCE_DIR SINK_TYPE SINK_DIR

Example:
python -m pywws.datastoretransfer filedata c:\weather_data sqlite3data d:\weather

This can be used to convert from the default file base storage system to an
SQL based sorage system, or back. The transfer will overwrite existing data
in place which may leave existing data in the destination if the incoming data
does not overlap (i.e. source data is newer than the destination). This is a
risky way to merge datastores together. Otherwise, its recommended to use the
optional -c argument to ensure the destination is cleared first.
You may choose the same storage module for both source and destination
with different directories, and this is the equivalent of simply copying the
data but will build the underlying files from scratch. However, copying the
files by hand is likely to be faster.

Config files such as weather.ini, and folders such as templates etc.
are not copied, so please ensure you consider seperately if required.
"""

from __future__ import absolute_import, print_function

import argparse
import importlib
import logging

import pywws.logger

logger = logging.getLogger(__name__)
pywws.logger.setup_handler(1)

def monitor(i):
    """Given an iterator, yields data from it
    but prints progress every 10,000 records"""
    count = 0
    for x in i:
        count+=1
        if count % 10000 == 0:
            logger.info("%d records so far, current record is %s",
                count, x["idx"])
        yield x

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="""Copy pywws data from one storage system to another.
        You must specify the pywws data module, and the path for both
        the source data set, and the destination data set.""")
    parser.add_argument("-c",
        help="Clear the existing destination datastore before transfer",
        action="store_true", dest="clearfirst")
    parser.add_argument("SourceType",
        help="The source storage system type")
    parser.add_argument("SourceDir",
        help="The source directory")
    parser.add_argument("SinkType",
        help="The destination storage system type")
    parser.add_argument("SinkDir",
        help="The destination directory")

    args = parser.parse_args()
    source_type = args.SourceType
    sink_type = args.SinkType
    source_dir = args.SourceDir
    sink_dir = args.SinkDir
    clearfirst=args.clearfirst

    if source_type == sink_type and source_dir == sink_dir:
        raise ValueError("You have specified the same source and sink")

    Source = importlib.import_module("."+source_type, package="pywws")
    Sink = importlib.import_module("."+sink_type, package="pywws")

    RawSink = Sink.RawStore(sink_dir)
    if clearfirst:
        logger.info("Clearing destination Raw Data...")
        RawSink.clear()
    logger.info("Transfering Raw Data...")
    RawSink.update(monitor(Source.RawStore(source_dir)))
    RawSink.flush()

    CalibSink = Sink.CalibStore(sink_dir)
    if clearfirst:
        logger.info("Clearing destination Calibrated Data...")
        CalibSink.clear()
    logger.info("Transfering Calibrated Data...")
    CalibSink.update(monitor(Source.CalibStore(source_dir)))
    CalibSink.flush()

    HourlySink = Sink.HourlyStore(sink_dir)
    if clearfirst:
        logger.info("Clearing destination Hourly Data...")
        HourlySink.clear()
    logger.info("Transfering Hourly Data...")
    HourlySink.update(monitor(Source.HourlyStore(source_dir)))
    HourlySink.flush()

    DailySink = Sink.DailyStore(sink_dir)
    if clearfirst:
        logger.info("Clearing destination Daily Data...")
        DailySink.clear()
    logger.info("Transfering Daily Data...")
    DailySink.update(monitor(Source.DailyStore(source_dir)))
    DailySink.flush()

    MonthlySink = Sink.MonthlyStore(sink_dir)
    if clearfirst:
        logger.info("Clearing destination Monthly Data...")
        MonthlySink.clear()
    logger.info("Transfering Monthly Data...")
    MonthlySink.update(monitor(Source.MonthlyStore(source_dir)))
    MonthlySink.flush()

    logger.info("Done!")