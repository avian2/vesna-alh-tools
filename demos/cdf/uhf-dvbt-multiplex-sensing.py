from vesna import cdf

import os
import string
import sys
import time

def main():
	f = open("uhf-dvbt-multiplex-sensing.cdf")
	e = cdf.CDFExperiment.load(f)

	start_time = time.time() + 15
	end_time = start_time + 30

	i = cdf.CDFExperimentIteration(start_time, end_time)
	e.run(i)

	e.save_all()

main()
