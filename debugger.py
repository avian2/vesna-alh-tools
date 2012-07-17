import alh
import binascii
import re
import serial
import string
import struct
import sys
import time

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

		#print "total size:", total_size

		p = 0
		max_read_size = 512
		data = ""

		while p < total_size:
			chunk_size = min(max_read_size, total_size - p)

			#if p < total_size - chunk_size*2:
			#	p += max_read_size
			#	continue

			#print "start", p
			#print "size", chunk_size

			chunk_data_crc = self.alh.get("sensing/slotDataBinary", "id=%d&start=%d&size=%d" % (
				self.slot_id, p, chunk_size))

			#print len(chunk_data_crc)
			#print repr(chunk_data_crc)

			chunk_data = chunk_data_crc[:-4]

			#print "len", len(chunk_data)
			
			their_crc = struct.unpack("i", chunk_data_crc[-4:])[0]
			our_crc = binascii.crc32(chunk_data)

			if(their_crc != our_crc):
				raise alh.CRCError

			data += chunk_data

			p += max_read_size

		return self._decode(data)

def test_spectrum_sensing():

	#f = serial.Serial("/dev/ttyUSB1", 115200, timeout=10)
	#coor = alh.ALHTerminal(f)
	#nde7 = alh.ALHProxy(coor, 1)

	coor = alh.ALHWeb("http://194.249.231.26:9002/communicator")

	addrs = [ 36, 37, 29, 41, 43, 40 ]
	nodes = [ alh.ALHProxy(coor, addr) for addr in addrs ]

	coor._log = log


	coor.post("prog/firstcall", "1")
	for node in nodes:
		node.post("prog/firstcall", "1")

	return

	#for node in nodes:
	#	node.get("sensing/deviceConfigList")

#	node8req = ""
#	node7req = ""
#
#	for n in xrange(8):
#		node8req += "in %d sec for 1 sec with dev 0 conf 0 channel %d power 0\r\n" % (5 + 0 + n, n*30)
#		node7req += "in %d sec for 1 sec with dev 0 conf 0 channel %d power 0\r\n" % (5 + 7 - n, n*30)
#
#	vesna.post_remote(8, "generator/program", node8req)
#	vesna.post_remote(7, "generator/program", node7req)



	#vesna.post_remote(8, "generator/program", 
	#		"in 5 sec for 10 sec with dev 0 conf 0 channel 40 power 0\r\n"
	#		"in 15 sec for 10 sec with dev 0 conf 0 channel 80 power 0\r\n"
	#		"in 25 sec for 10 sec with dev 0 conf 0 channel 120 power 0\r\n"
	#		"in 35 sec for 10 sec with dev 0 conf 0 channel 160 power 0\r\n"
	#		"in 45 sec for 10 sec with dev 0 conf 0 channel 200 power 0\r\n"
	#		)
	
	experiments = [
		ALHSpectrumSensingExperiment(node,
			time_start = 2,
			time_duration = 60,
			device = 0,
			config = 0,
			ch_start = 0,
			ch_step = 1,
			ch_stop = 255,
			slot_id = 3)
		for node in nodes ]

	for experiment in experiments:
		experiment.program()

	for n, experiment in enumerate(experiments):
		while not experiment.is_complete():
			print "waiting..."
			time.sleep(1)

		print "experiment is finished. retrieving data."

		sweeps = experiment.retrieve()

		outf = open("large_%d" % n, "w")
		for sweep in sweeps:
			for dbm in sweep:
				outf.write("%f\n" % (dbm,))
			outf.write("\n")
		outf.close()

def main():
	test_spectrum_sensing()
	return

main()
