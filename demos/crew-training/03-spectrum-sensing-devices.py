# This demo shows how to query a selection of nodes in the Log-a-tec
# industrial zone for mounted spectrum sensing devices and available pre-set
# configurations.

import logging
from vesna import alh

def main():
	#logging.basicConfig(level=logging.INFO)

	coor = alh.ALHWeb("https://crn.log-a-tec.eu/communicator", 10001)

	# Nodes in Log-a-tec are equipped with different spectrum sensing
	# hardware. Here, the network addresses are chosen so that at the
	# time of writing these should cover CC1101, CC2500 and TDA18219
	# receivers.
	for addr in [8, 25, 19]:
		node = alh.ALHProxy(coor, addr)

		print("Spectrum sensing configurations for node %d:" % (addr,))
		print(node.get("sensing/deviceConfigList"))

main()
