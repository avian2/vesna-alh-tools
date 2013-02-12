# This demo shows how to use tranceiver hardware on VESNA nodes for signal
# generation. A simple signal generation interface is exposed through ALH
# resources. Code below uses convenience objects from the
# vesna.alh.signalgenerator module to access them. 

import logging
import time
from vesna import alh

from vesna.alh.signalgenerator import SignalGenerator, SignalGeneratorProgram

def main():
	# Turn on logging so that we can see ALH requests happening in the
	# background.
	logging.basicConfig(level=logging.INFO)

	coor = alh.ALHWeb("https://crn.log-a-tec.eu/communicator", 10001)

	# Node 16 is equipped with an 2.4 GHz tranceiver (CC2500 on
	# SNE-ISMTV-24) that is capable of transmitting on the 2.4 GHz ISM
	# band.
	node = alh.ALHProxy(coor, 16)

	# We the ALHProxy object with a SignalGenerator object that provides an
	# convenient interface to the signal generation functionality.
	generator = SignalGenerator(node)

	# Get a ConfigList object that contains a list of device configurations
	# supported by the chosen transmitter node.
	config_list = generator.get_config_list()

	# ConfigList.get_tx_config() method will automatically choose
	# a device and hardware configuration that can be used to transmit on
	# the requested frequency. It returns an instance of TxConfig class
	# that describes all settings for signal generation.
	#
	# We request a transmission at 2.425 GHz with 0 dBm.
	tx_config = config_list.get_tx_config(2425e6, 0)
	if tx_config is None:
		raise Exception("Node can not transmit at the specified frequency and/or power.")

	# SignalGeneratorProgram object joins the transmit config with timing
	# information. Here we specify that we want to start the transmission 5
	# seconds from now and that the transmission should be 30 seconds long.
	now = time.time()
	program = SignalGeneratorProgram(tx_config, now + 5, 30)

	generator.program(program)

main()
