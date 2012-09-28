#!/bin/bash

set -e

BASENAME=`basename $0`

CLUSTER=`echo "$BASENAME"|sed 's/_.*//'`
NODE_ID=`echo "$BASENAME"|sed 's/^.*_node_\([0-9]\+\)_.*$/\1/'`
LABEL=`echo "$BASENAME"|sed 's/.*_//;s/\..*$//'`

case $1 in
	config)
		echo "host_name node$NODE_ID.$CLUSTER"
		cat "$datadir/config_$LABEL"
		exit 0
		;;
	*)
		cat "$datadir/node_${NODE_ID}_$LABEL"
		exit 0
		;;
esac
