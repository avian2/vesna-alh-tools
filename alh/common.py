import alh
import serial
import string

def add_communication_options(parser):
	parser.add_option("-U", "--url", dest="url", metavar="URL",
			help="Use URL for communication with coordinator")
	parser.add_option("-u", "--cluster", dest="cluster_id", metavar="ID", type="int",
			help="Cluster ID to pass to the web API")

	parser.add_option("-D", "--device", dest="device", metavar="PATH",
			help="Use serial terminal for communication with coordinator")

def log(msg):
	if all(c in string.printable for c in msg):
		print msg.decode("ascii", "ignore")
	else:
		print "Unprintable packet"

def get_coordinator(options):
	if options.url and not options.device:
		coordinator = alh.ALHWeb(options.url, options.cluster_id)
	elif options.device and not options.url:
		f = serial.Serial(options.device, 115200, timeout=10)
		coordinator = alh.ALHTerminal(f)
	else:
		raise Exception("Please give either -U or -D option")

	coordinator._log = log
	return coordinator
