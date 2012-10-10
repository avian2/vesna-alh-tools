import binascii
import re
import struct
import time
import alh
import pickle

class Sweep:
	def __init__(self):
		self.data = []

class SpectrumSensingRun:
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

		relative_time = max(0, int(self.time_start - time.time()))

		self.alh.post("sensing/program",
			"in %d sec for %d sec with dev %d conf %d ch %d:%d:%d to slot %d" % (
				relative_time,
				self.time_duration,
				self.device,
				self.config,
				self.ch_start,
				self.ch_step,
				self.ch_stop,
				self.slot_id))

	def is_complete(self):
		if time.time() < self.time_start + self.time_duration:
			return False
		else:
			resp = self.alh.get("sensing/slotInformation", "id=%d" % (self.slot_id,))
			return "status=COMPLETE" in resp

	def _decode(self, data):
		sweep_len = len(range(self.ch_start, self.ch_stop, self.ch_step))
		line_len = 2*sweep_len + 4

		sweeps = []
		sweep = Sweep()

		for n in xrange(0, len(data), 2):
			datum = data[n:n+2]
			if len(datum) != 2:
				continue

			if(n % line_len == 0):
				# got a time-stamp
				t = data[n:n+4]
				tt = struct.unpack("<I", t)[0]
				assert(not sweep.data)
				sweep.timestamp = tt
				continue

			if(n % line_len == 2):
				# second part of a time-stamp, just ignore
				assert(len(sweep.data) == 0)
				continue

			dbm = struct.unpack("h", datum)[0]*1e-2
			sweep.data.append(dbm)

			if(len(sweep.data) >= sweep_len):
				sweeps.append(sweep)
				sweep = Sweep()

		if(sweep.data):
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

			chunk_data = chunk_data_crc[:-4]

			#print "len", len(chunk_data)
			
			their_crc = struct.unpack("i", chunk_data_crc[-4:])[0]
			our_crc = binascii.crc32(chunk_data)

			if(their_crc != our_crc):
				raise alh.CRCError

			data += chunk_data

			p += max_read_size

		return self._decode(data)

class MultiNodeSpectrumSensingRun:
	def __init__(self, nodes, *args, **kwargs):

		self.runs = [ 
			SpectrumSensingRun(node, *args, **kwargs)
			for node in nodes ]

	def program(self):
		for run in self.runs:
			run.program()

	def is_complete(self):
		for run in self.runs:
			run.alh.get("sensing/program")
		return all(run.is_complete() for run in self.runs)

	def retrieve(self):
		return [ run.retrieve() for run in self.runs ]

class SignalGenerationRun:
	def __init__(self, alh, time_start, time_duration, 
			device, config, channel, power):

		self.alh = alh

		self.time_start = time_start
		self.time_duration = time_duration
		self.device = device
		self.config = config
		self.channel = channel
		self.power = power

	def program(self):
		relative_time = max(0, int(self.time_start - time.time()))

		self.alh.post("generator/program",
			"in %d sec for %d sec with dev %d conf %d channel %d power %d" % (
				relative_time,
				self.time_duration,
				self.device,
				self.config,
				self.channel,
				self.power))

class MultiNodeSignalGenerationRun:
	def __init__(self, nodes, *args, **kwargs):

		self.runs = [
			SignalGenerationRun(node, *args, **kwargs)
			for node in nodes ]

	def program(self):
		for run in self.runs:
			run.program()

def write_results(path, results, multinoderun):

	for n, (result, run) in enumerate(zip(results, multinoderun.runs)):

		if hasattr(run.alh, "addr"):
			name = "node_%d.dat" % (run.alh.addr,)
		else:
			name = "run_%d.dat" % (n,)

		fn = "%s/%s" % (path, name)
		outf = open(fn, "w")
		outf.write("# t [s]\tf [Hz]\tP [dBm]\n")

		sweep_len = len(range(run.ch_start, run.ch_stop, run.ch_step))
		for sweepnr, sweep in enumerate(result):
			# TODO in case multiple sweeps have been done in the same second,
			#	properly extrapolate
			assert(isinstance(sweep, Sweep))
			for dbmn, dbm in enumerate(sweep.data):

				time = float(sweep.timestamp) + 1.0/sweep_len * dbmn

				channel = run.ch_start + run.ch_step * dbmn
				assert channel < run.ch_stop

				outf.write("%f\t%f\t%f\n" % (time, channel, dbm))

			outf.write("\n")

		outf.close()
