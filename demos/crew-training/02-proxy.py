# Since the HTTP API terminates at the coordinator and the ALH is an
# point-to-point protocol, we cannot access resources on sensor nodes
# directly. 
#
# This demo shows how to perform a "GET sensor/mcuTemp" request on a sensor
# node 19 using the coordinator as a proxy.

import logging
from vesna import alh

def main():
	logging.basicConfig(level=logging.INFO)

	# Establish a connection with the coordinator and return a
	# coordinator object.
	coor = alh.ALHWeb("https://crn.log-a-tec.eu/communicator", 10001)

	# Get a sensor node object by proxying request through the coordinator.
	# The node object supports GET and POST requests in the same way as
	# the coordinator object.
	node19 = alh.ALHProxy(coor, 19)

	# Read out the value from the integrated temperature sensor.
	# Temperature sensors are usually not calibrated in the Log-a-tec
	# testbed, so this value might be significantly off.
	print node19.get("sensor/mcuTemp")

main()
