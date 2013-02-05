from vesna import alh
from vesna.alh.spectrumsensor import SpectrumSensor, SpectrumSensorProgram
from vesna.alh.common import log

import os
import string
import sys
import time

def get_communicator_url():
	return "https://crn.log-a-tec.eu/communicator"

def main():
	coor_industrial_zone = alh.ALHWeb(get_communicator_url(), 10001)
	coor_industrial_zone._log = log

	coor_kabelnet = alh.ALHWeb(get_communicator_url(), 10004)
	coor_kabelnet._log = log

	#coor_jsi_test = alh.ALHWeb(get_communicator_url(), 9502)
	#coor_jsi_test._log = log

	nodes = [	#alh.ALHProxy(coor_jsi_test, 18),
			alh.ALHProxy(coor_industrial_zone, 19),
			alh.ALHProxy(coor_industrial_zone, 20),
			alh.ALHProxy(coor_kabelnet, 47),
	]

	for node in nodes:
		node.post("prog/firstCall", "1")

	sensors = map(SpectrumSensor, nodes)

	config_list = sensors[0].get_config_list()

	sweep_config = config_list.get_sweep_config(
			start_hz=546000000, stop_hz=586000000, step_hz=500000)
	assert sweep_config is not None

	time_start = time.time() + 15
	program = SpectrumSensorProgram(sweep_config, time_start, time_duration=30, slot_id=5)

	for sensor in sensors:
		sensor.program(program)

	for sensor in sensors:
		while not sensor.is_complete(program):
			print "waiting..."
			time.sleep(2)

			if time.time() > (program.time_start + program.time_duration + 30):
				raise Exception("Something went wrong")

		print "experiment is finished. retrieving data."

		result = sensor.retrieve(program)

		try:
			os.mkdir("data")
		except OSError:
			pass

		result.write("data/node_%d.dat" % (sensor.alh.addr,))

main()
