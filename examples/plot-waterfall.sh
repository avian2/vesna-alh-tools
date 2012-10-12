#!/bin/sh
# arg 1: filename to plot
gnuplot << EOF

set title '$1'
set xlabel "f [MHz]"
set ylabel "t [s]"
set cblabel "P [dBm]"
set grid
unset key
set pm3d map corners2color c1
splot "$1" using (\$2/1e6):1:3
pause mouse
EOF
#
