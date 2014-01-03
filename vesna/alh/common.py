import logging
from vesna import alh
import serial
import sys

def add_communication_options(parser):
	parser.add_option("-U", "--url", dest="url", metavar="URL",
			help="Use URL for communication with coordinator")
	parser.add_option("-u", "--cluster", dest="cluster_id", metavar="ID", type="int",
			help="Cluster ID to pass to the web API")

	parser.add_option("-D", "--device", dest="device", metavar="PATH",
			help="Use serial terminal for communication with coordinator")
	parser.add_option("-v", "--verbosity", dest="verbosity", metavar="LEVEL",
			help="Set verbosity level (debug, info, warning, error)")

def get_coordinator(options):
	if options.url and not options.device:
		coordinator = alh.ALHWeb(options.url, options.cluster_id)
	elif options.device and not options.url:
		f = serial.Serial(options.device, 115200, timeout=180)
		coordinator = alh.ALHTerminal(f)
	else:
		raise Exception("Please give either -U or -D option")

	if options.verbosity:
		level = getattr(logging, options.verbosity.upper(), None)
		if not isinstance(level, int):
			raise Exception("Invalid verbosity level: %s" % (level,))
	else:
		level = logging.INFO

	logging.basicConfig(level=level)

	return coordinator
