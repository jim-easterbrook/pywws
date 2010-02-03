#!/bin/sh

# extract marked strings from Python files

xgettext --language=Python --output=pywws.pot ../*.py
