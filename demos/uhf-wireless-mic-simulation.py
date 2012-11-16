from vesna import alh
from vesna.alh.spectrumsensor import SpectrumSensor, SpectrumSensorProgram
from vesna.alh.signalgenerator import SignalGenerator, SignalGeneratorProgram, TxConfig
from vesna.alh.common import log

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

	time_start = time.time() + 30

	# Set up transmissions

	su1 = SignalGenerator(alh.ALHProxy(coor_industrial_zone, 10))
	su2 = SignalGenerator(alh.ALHProxy(coor_industrial_zone, 8))
	mic = SignalGenerator(alh.ALHProxy(coor_industrial_zone, 7))

	config_list = su1.get_config_list()

	tx_config = config_list.get_tx_config(0, 0)

	mic.program( SignalGeneratorProgram(
		config_list.get_tx_config(f_hz=790e6, power_dbm=0),
		time_start=time_start+30,
		time_duration=40) )

	mic.program( SignalGeneratorProgram(
		config_list.get_tx_config(f_hz=807e6, power_dbm=0),
		time_start=time_start+80,
		time_duration=40) )

	su1.program( SignalGeneratorProgram(
		config_list.get_tx_config(f_hz=787e6, power_dbm=0),
		time_start=time_start,
		time_duration=35) )

	su1.program( SignalGeneratorProgram(
		config_list.get_tx_config(f_hz=780e6, power_dbm=0),
		time_start=time_start+35,
		time_duration=90) )

	su2.program( SignalGeneratorProgram(
		config_list.get_tx_config(f_hz=795e6, power_dbm=0),
		time_start=time_start,
		time_duration=35) )

	su2.program( SignalGeneratorProgram(
		config_list.get_tx_config(f_hz=800e6, power_dbm=0),
		time_start=time_start+35,
		time_duration=50) )

	su2.program( SignalGeneratorProgram(
		config_list.get_tx_config(f_hz=797e6, power_dbm=0),
		time_start=time_start+85,
		time_duration=35) )

	# Set up spectrum sensing

	sensor_node_ids = [ 19 ]

	sensor_nodes = [ alh.ALHProxy(coor_industrial_zone, id) for id in sensor_node_ids ]
	sensors = [ SpectrumSensor(sensor_node) for sensor_node in sensor_nodes ]

	config_list = sensors[0].get_config_list()
	sweep_config = config_list.get_sweep_config(
			start_hz=770000000, stop_hz=820000000, step_hz=400000)
	
	# -1 below is a work-around for an off-by-one error somewhere in the spectrum sensing
	# resource handler
	sweep_config.num_channels -= 1

	program = SpectrumSensorProgram(sweep_config, time_start, time_duration=120, slot_id=5)

	for sensor in sensors:
		sensor.program(program)

	
	# Wait for the experiment to finish

	for sensor in sensors:
		while not sensor.is_complete(program):
			print "waiting..."
			time.sleep(2)

			if time.time() > (program.time_start + program.time_duration + 60):
				raise Exception("Something went wrong")

		print "experiment is finished. retrieving data."

		result = sensor.retrieve(program)

		try:
			os.mkdir("data")
		except OSError:
			pass

		result.write("data/node_%d.dat" % (sensor.alh.addr,))

main()
