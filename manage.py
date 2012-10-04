#!/usr/bin/bpython -i
import alh.common
import alh.alh
from optparse import OptionParser, OptionGroup

def hello(options):
	print "Hi."
	print
	if options.url and not options.device:
		print "You are using a remote VESNA cluster at "
		print options.url, "port", options.cluster_id
	elif options.device and not options.url:
		print "You are using a local VESNA cluster at ", options.device
	print
	print "Coordinator is 'coor'. Node objects can be obtained through 'node(addr)'."
	print

	print "Have fun!"

def main():
	global coor
	parser = OptionParser(usage="%prog [options]")

	alh.common.add_communication_options(parser)
	(options, args) = parser.parse_args()

	coor = alh.common.get_coordinator(options)
	coor.post("prog/firstcall", "1")

	hello(options)

def node(addr):
	global coor
	return alh.alh.ALHProxy(coor, addr)

main()
