from alh import alh
from alh.spectrum import *
from alh.common import log
import os
import string
import sys
import time

def get_communicator_url():
	try:
		credentials = open("credentials").read().strip() + "@"
	except IOError:
		credentials = ""

	return "https://%scrn.log-a-tec.eu/communicator" % (credentials,)

def main():
	coor_industrial_zone = alh.ALHWeb(get_communicator_url(), 10001)
	coor_industrial_zone._log = log

	coor_kabelnet = alh.ALHWeb(get_communicator_url(), 10004)
	coor_kabelnet._log = log

	node_19 = alh.ALHProxy(coor_industrial_zone, 19)
	node_20 = alh.ALHProxy(coor_industrial_zone, 20)
	node_47 = alh.ALHProxy(coor_kabelnet, 47)

	time_start = time.time() + 15

	experiment = MultiNodeSpectrumSensingRun(
			[node_19, node_20, node_47],
			time_start = time_start,
			time_duration = 20,
			device_id = 0,
			config_id = 0,
			ch_start = 76000,
			ch_step = 500,
			ch_stop = 116000,
			slot_id = 5)

	experiment.program()

	while not experiment.is_complete():
		print "waiting..."
		time.sleep(2)

	print "experiment is finished. retrieving data."

	results = experiment.retrieve()

	try:
		os.mkdir("data")
	except OSError:
		pass
	write_results("data", results, experiment)

main()
