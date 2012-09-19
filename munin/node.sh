#!/bin/bash

set -e

NODE_ID=`basename $0|sed 's/^.*_\([0-9]\+\)_.*$/\1/'`
LABEL=`basename $0|sed 's/.*_//;s/\..*$//'`

case $1 in
	config)
		echo "host_name node$NODE_ID"
		cat "$datadir/config_$LABEL"
		exit 0
		;;
	*)
		cat "$datadir/node_${NODE_ID}_$LABEL"
		exit 0
		;;
esac
