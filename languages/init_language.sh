#!/bin/sh

# create a language template from extracted strings

if [ "$1" ]; then
  msginit --input=pywws.pot --locale=$1
else
  msginit --input=pywws.pot
  fi
