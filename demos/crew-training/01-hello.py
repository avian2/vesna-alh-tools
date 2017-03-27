# This demo establishes connection with Log-a-tec coordinator (industrial
# zone cluster) over the HTTP REST API, performs a GET request to the
# "hello" resource and prints out the response.

import logging
from vesna import alh

def main():
	# Set up logging to show informational messages. It's always useful to
	# see what is going on behind the scenes.
	logging.basicConfig(level=logging.INFO)

	# A single API end point can connect to multiple clusters, so we
	# have to supply a cluster ID in addition to the end point URL.
	#
	# For Log-a-tec industrial zone cluster, cluster ID is 10001.
	coor = alh.ALHWeb("http://193.2.205.189:9000/communicator", "/dev/ttyS1")

	# This should print out something similar to
	# "Hello Application version 2.16"
	print coor.get("hello")
	print coor.get("sensor/mcuTemp")

main()
