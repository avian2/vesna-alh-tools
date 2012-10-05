#!/bin/sh
# arg 1: filename to plot
gnuplot << EOF

set title '$1'
set timefmt "%s"
set pm3d map corners2color c1
splot "$1" using 2:1:3
pause mouse
EOF
#
