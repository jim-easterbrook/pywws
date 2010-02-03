#!/bin/sh

# convert a .po file to a .mo compiled language file

src=$1.po
if [ ! -f $src ]; then
  echo "Language file $src not found"
  exit 1
  fi
dest=../locale/$1/LC_MESSAGES
mkdir -p $dest
msgfmt --output-file=$dest/pywws.mo $src
