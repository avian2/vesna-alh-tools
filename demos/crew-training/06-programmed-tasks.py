# This demo shows how to program signal generation and spectrum sensing tasks
# in advance. This allows experimenter to set up multiple nodes in the testbed
# to perform simultaneous tasks.

import logging
import time
from vesna import alh

from vesna.alh.signalgenerator import SignalGenerator, SignalGeneratorProgram
from vesna.alh.spectrumsensor import SpectrumSensor, SpectrumSensorProgram

def main():
	# Turn on logging so that we can see ALH requests happening in the
	# background.
	logging.basicConfig(level=logging.INFO)

	coor = alh.ALHWeb("https://crn.log-a-tec.eu/communicator", 10001)

	# Nodes 16 and 17 are equipped with an 2.4 GHz tranceiver (CC2500 on
	# SNE-ISMTV-24) that is capable of transmitting and receiving on the
	# 2.4 GHz ISM band.
	node16 = alh.ALHProxy(coor, 16) 
	node17 = alh.ALHProxy(coor, 17)

	# We will use node 16 as a signal generator. We wrap its ALHProxy
	# object with a SignalGenerator object for convenience.
	generator = SignalGenerator(node16)
	
	# Set up a transmission configuration for 2.425 GHz and 0 dBm
	generator_config_list = generator.get_config_list()

	tx_config = generator_config_list.get_tx_config(2425e6, 0)
	if tx_config is None:
		raise Exception("Node can not scan specified frequency range.")

	# We will use node 17 as a spectrum sensor. Again, we wrap it with a
	# SpectrumSensor object for convenience.
	sensor = SpectrumSensor(node17)

	# We set up a frequency sweep configuration covering 2.40 GHz to 2.45
	# GHz band with 400 kHz steps.
	sensor_config_list = sensor.get_config_list()

	sweep_config = sensor_config_list.get_sweep_config(2400e6, 2450e6, 400e3)
	if sweep_config is None:
		raise Exception("Node can not scan specified frequency range.")

	# Take note of current time.
	now = time.time()

	# SignalGeneratorProgram and SpectrumSensorProgram objects allow us to
	# program signal generation and spectrum sensing tasks in advance. 
	#
	# In this case, we setup a signal generation task using the
	# configuration we prepared above starting 10 seconds from now and
	# lasting for 20 seconds.
	#
	# Similarly for spectrum sensing, we setup a task using frequency sweep
	# we prepared above starting 5 seconds from now and lasting for 30
	# seconds. Results of the measurement will be stored in slot 4.
	generator_program = SignalGeneratorProgram(tx_config, now + 10, 20)
	sensor_program = SpectrumSensorProgram(sweep_config, now + 5, 30, 4)

	# Now actually send instructions over the management network to nodes
	# in the testbed.
	generator.program(generator_program)
	sensor.program(sensor_program)

	# Query the spectrum sensing node and wait until the task has been
	# completed.
	while not sensor.is_complete(sensor_program):
		print "waiting..."
		time.sleep(2)

	# Retrieve spectrum sensing results. This might take a while since the
	# management mesh network is slow.
	result = sensor.retrieve(sensor_program)

	# Write results into a CSV file.
	result.write("06-programmed-sensing.dat")

main()
