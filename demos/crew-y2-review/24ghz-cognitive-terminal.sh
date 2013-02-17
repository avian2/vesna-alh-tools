#!/bin/bash

set -e

if [ "$#" -ne 1 ]; then
	echo "USAGE: $0 path-to-result-directory"
	exit 1
fi

NAME=`basename $0 .sh`
DESTDIR="$1"

if [ ! -d "$DESTDIR" ]; then
	mkdir -p "$DESTDIR"
fi

python $NAME.py
gnuplot $NAME.gnuplot
mv data/*.{dat,png} "$DESTDIR"
