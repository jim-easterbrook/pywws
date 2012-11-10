#!/usr/bin/env python

"""
Common code for logging info and errors.
"""

import logging
import logging.handlers

def ApplicationLogger(verbose, logfile=None):
    logger = logging.getLogger('')
    if logfile:
        logger.setLevel(max(logging.ERROR - (verbose * 10), 1))
        handler = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=128*1024, backupCount=3)
        datefmt = '%Y-%m-%d %H:%M:%S'
    else:
        logger.setLevel(max(logging.WARNING - (verbose * 10), 1))
        handler = logging.StreamHandler()
        datefmt = '%H:%M:%S'
    handler.setFormatter(
        logging.Formatter('%(asctime)s:%(name)s:%(message)s', datefmt))
    logger.addHandler(handler)
    return logger
