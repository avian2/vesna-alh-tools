import alh
import binascii
import serial
import string
import struct
from optparse import OptionParser, OptionGroup

def log(msg):
	if all(c in string.printable for c in msg):
		print msg.decode("ascii", "ignore")
	else:
		print "Unprintable packet"

def upload_firmware(target, firmware, slot_id):
	target.post("prog/nextFirmwareSlotId", "%d" % (slot_id,))
	target.post("prog/nextFirmwareSize", "%d" % (len(firmware),))
	target.post("prog/nextEraseSlotId", "%d" % (slot_id,))

	chunk_size = 512
	total_size = len(firmware)
	chunk_num = 0
	p = 0
	while p < total_size:
		chunk_data = struct.pack(">i", chunk_num) + firmware[p:p+chunk_size]
		if len(chunk_data) != 516:
			chunk_data += "\xff" * (516 - len(chunk_data))
			
		chunk_data_crc = binascii.crc32(chunk_data)

		chunk = chunk_data + struct.pack(">i", chunk_data_crc)

		target.post("firmware", chunk)

		p += chunk_size
		chunk_num += 1

	target.post("prog/nextFirmwareCrc", "%d" % (binascii.crc32(firmware),))

def reboot_firmware(target, slot_id):
	target.post("prog/setupBootloaderForReprogram", "%d" % (slot_id,))
	target.post("prog/doRestart", "1")

def main():
	parser = OptionParser(usage="%prog [options]")

	parser.add_option("-H", "--host", dest="host", metavar="HOST",
			help="Use HOST for communication with coordinator")
	parser.add_option("-D", "--device", dest="device", metavar="PATH",
			help="Use serial terminal for communication with coordinator")

	parser.add_option("-n", "--node", dest="node", metavar="ADDR", type="int",
			help="Reprogram node with ZigBit address ADDR")
	parser.add_option("-c", "--coordinator", dest="coordinator", action="store_true",
			help="Reprogram coordinator")

	parser.add_option("-i", "--input", dest="input", metavar="PATH",
			help="PATH to firmware to upload")

	parser.add_option("-s", "--slot", dest="slot_id", metavar="ID", default=1,
			help="Use SD card slot ID for upload")

	(options, args) = parser.parse_args()

	if options.host and not options.device:
		coordinator = alh.ALHWeb("http://%s/communicator" % (options.host,))
	elif options.device and not options.host:
		f = serial.Serial(options.device, 115200, timeout=10)
		coordinator = alh.ALHTerminal(f)
	else:
		print "Please give either -H or -D option"
		return -1

	coordinator._log = log

	coordinator.post("prog/firstcall", "1")

	if options.coordinator and not options.node:
		target = coordinator
	elif options.node and not options.coordinator:
		node = alh.ALHProxy(coordinator, options.node)
		node.post("prog/firstcall", "1")
		target = node
	else:
		print "Please give either -n or -c option"
		return -1

	firmware = open(options.input).read()

	upload_firmware(target, firmware, options.slot_id)
	reboot_firmware(target, options.slot_id)

main()
