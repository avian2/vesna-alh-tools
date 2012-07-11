import binascii
import re
import serial
import struct
import time
import alh

class ALHSpectrumSensingExperiment:
	def __init__(self, alh, time_start, time_duration, 
			device, config, ch_start, ch_step, ch_stop, slot_id):

		self.alh = alh

		self.time_start = time_start
		self.time_duration = time_duration
		self.device = device
		self.config = config
		self.ch_start = ch_start
		self.ch_step = ch_step
		self.ch_stop = ch_stop
		self.slot_id = slot_id

	def program(self):
		self.alh.post("sensing/freeUpDataSlot", "1", "id=%d" % (self.slot_id))
		self.alh.post("sensing/program",
			"in %d sec for %d sec with dev %d conf %d ch %d:%d:%d to slot %d" % (
				self.time_start,
				self.time_duration,
				self.device,
				self.config,
				self.ch_start,
				self.ch_step,
				self.ch_stop,
				self.slot_id))

	def is_complete(self):
		resp = self.alh.get("sensing/slotInformation", "id=%d" % (self.slot_id,))
		return "status=COMPLETE" in resp

	def _decode(self, data):
		sweep_len = len(range(self.ch_start, self.ch_stop, self.ch_step))

		sweeps = []
		sweep = []

		for n in xrange(0, len(data), 2):
			datum = data[n:n+2]
			if len(datum) != 2:
				continue

			dbm = struct.unpack("h", datum)[0]*1e-2
			sweep.append(dbm)

			if(len(sweep) >= sweep_len):
				sweeps.append(sweep)
				sweep = []

		if(sweep):
			sweeps.append(sweep)

		return sweeps

	def retrieve(self):
		resp = self.alh.get("sensing/slotInformation", "id=%d" % (self.slot_id,))
		assert("status=COMPLETE" in resp)

		g = re.search("size=([0-9]+)", resp)
		total_size = int(g.group(1))

		p = 0
		max_read_size = 512
		data = ""
		while p < total_size:
			chunk_size = min(max_read_size, total_size - p)

			chunk_data_crc = self.alh.get("sensing/slotDataBinary", "id=%d&start=%d&size=%d" % (
				self.slot_id, p, chunk_size))

			chunk_data = chunk_data_crc[:-4]
			
			their_crc = struct.unpack("i", chunk_data_crc[-4:])[0]
			our_crc = binascii.crc32(chunk_data)

			if(their_crc != our_crc):
				raise alh.CRCError

			data += chunk_data

			p += max_read_size

		return self._decode(data)

def upload_firmware(alh, firmware, slot_id):
	print alh.post("prog/nextFirmwareSlotId", "%d" % (slot_id,))
	print alh.post("prog/nextFirmwareSize", "%d" % (len(firmware),))
	print alh.post("prog/nextEraseSlotId", "%d" % (slot_id,))

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

		print alh.post("firmware", chunk)

		p += chunk_size
		chunk_num += 1

	print alh.post("prog/nextFirmwareCrc", "%d" % (binascii.crc32(firmware),))

def reboot_firmware(alh, slot_id):
	print alh.post("prog/setupBootloaderForReprogram", "%d" % (slot_id,))
	print alh.post("prog/doRestart", "1")

def main():
	#f = serial.Serial("/dev/ttyUSB1", 115200, timeout=10)
	#coor = ALHProtocol(f)
	coor = alh.ALHWeb("http://194.249.231.26:9002/communicator")

	nde7 = alh.ALHProxy(coor, 43)

	print coor.post("prog/firstcall", "1")
	print nde7.post("prog/firstcall", "1")

	#firmware = open("/home/avian/dev/vesna-drivers/Applications/Logatec/NodeSpectrumSensor/logatec_node_app.bin").read()
	#firmware = open("ttt").read()
	#upload_firmware(nde7, firmware, 13)
	#reboot_firmware(nde7, 13)
	#return

#	node8req = ""
#	node7req = ""
#
#	for n in xrange(8):
#		node8req += "in %d sec for 1 sec with dev 0 conf 0 channel %d power 0\r\n" % (5 + 0 + n, n*30)
#		node7req += "in %d sec for 1 sec with dev 0 conf 0 channel %d power 0\r\n" % (5 + 7 - n, n*30)
#
#	vesna.post_remote(8, "generator/program", node8req)
#	vesna.post_remote(7, "generator/program", node7req)

	print nde7.get("sensing/deviceConfigList")


	#vesna.post_remote(8, "generator/program", 
	#		"in 5 sec for 10 sec with dev 0 conf 0 channel 40 power 0\r\n"
	#		"in 15 sec for 10 sec with dev 0 conf 0 channel 80 power 0\r\n"
	#		"in 25 sec for 10 sec with dev 0 conf 0 channel 120 power 0\r\n"
	#		"in 35 sec for 10 sec with dev 0 conf 0 channel 160 power 0\r\n"
	#		"in 45 sec for 10 sec with dev 0 conf 0 channel 200 power 0\r\n"
	#		)
	
	exp = ALHSpectrumSensingExperiment(nde7,
			time_start = 2,
			time_duration = 60,
			device = 0,
			config = 0,
			ch_start = 0,
			ch_step = 1,
			ch_stop = 255,
			slot_id = 3)

	exp.program()

	while not exp.is_complete():
		print "waiting..."
		time.sleep(1)

	print "experiment is finished. retrieving data."

	sweeps = exp.retrieve()

	outf = open("out", "w")
	for sweep in sweeps:
		for dbm in sweep:
			outf.write("%f\n" % (dbm,))
		outf.write("\n")
	outf.close()

main()
