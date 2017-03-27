# This demo shows how to perform single frequency sweeps using spectrum sensing
# hardware on one node and plot them using matplotlib.
#
# Instead of accessing resources directly it uses convenience objects from
# the vesna.alh.spectrumsensor module.

import logging
from vesna import alh

from vesna.alh.spectrumsensor import SpectrumSensor

import numpy
from matplotlib import pyplot

def main():
	# Turn on logging so that we can see ALH requests happening in the
	# background.
	logging.basicConfig(level=logging.INFO)

	coor = alh.ALHWeb("https://crn.log-a-tec.eu/communicator", 10001)

	# Node 19 is equipped with an UHF receiver (TDA18219 on SNE-ISMTV-UHF)
	node = alh.ALHProxy(coor, 19) 

	# Node 17 is equipped with an 2.4 GHz receiver (CC2500 on SNE-ISMTV-24)
	#node = alh.ALHProxy(coor, 17)

	# Wrap an ALHProxy object with a SpectrumSensor object that provides an
	# convenient interface to spectrum sensing functionality of the node
	# exposed through ALH resources.
	sensor = SpectrumSensor(node)

	# Get a ConfigList object that contains a list of device configurations
	# supported by the chosen sensor node.
	config_list = sensor.get_config_list()

	# ConfigList.get_sweep_config() method will automatically choose
	# the best device and configuration that can cover the requested
	# frequency range.
	#
	# It returns an instance of SweepConfig class that describes all
	# the settings for a frequency sweep.
	#
	# First example defines a sweep starting at 550 MHz and ending at
	# 574 MHz with 2 MHz steps (use with node 19)
	#
	# Second example define a sweep starting at 2420 MHz and ending at
	# 2430 MHz with 400 kHz steps (use with node 17)
	sweep_config = config_list.get_sweep_config(550e6, 574e6, 1e6)
	#sweep_config = config_list.get_sweep_config(2420e6, 2430e6, 400e3)

	if sweep_config is None:
		raise Exception("Node can not scan specified frequency range.")

	pyplot.ion()

	while True:
		# Perform the sweep
		sweep = sensor.sweep(sweep_config)

		# Get the list of frequencies covered by the sweep
		f_hz = sweep_config.get_hz_list()

		# Convert list from Hz to MHz for nicer plot
		f_mhz = numpy.array(f_hz) / 1e6

		pyplot.clf()
		pyplot.grid()
		pyplot.xlabel("frequency [MHz]")
		pyplot.ylabel("power [dBm]")

		# Plot data
		pyplot.plot(f_mhz, sweep.data)

		pyplot.axis([min(f_mhz), max(f_mhz), -110, -50])
		pyplot.draw()

		pyplot.pause(1)

main()
