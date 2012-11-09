import alh
import binascii
import itertools
import re
import struct
import time

class Sweep:
	def __init__(self):
		self.data = []

class DeviceConfig:
	def __init__(self, id):
		self.id = id

	def ch_to_hz(self, ch):
		assert ch < self.num
		return self.base + self.spacing * ch

class SpectrumSensingRun:
	MAX_TIME_ERROR = 2.0

	def __init__(self, alh, time_start, time_duration, 
			device_id, config_id, ch_start, ch_step, ch_stop, slot_id):

		self.alh = alh

		self.time_start = time_start
		self.time_duration = time_duration
		self.device_id = device_id
		self.config_id = config_id
		self.ch_start = ch_start
		self.ch_step = ch_step
		self.ch_stop = ch_stop
		self.slot_id = slot_id

	def program(self):
		self.alh.post("sensing/freeUpDataSlot", "1", "id=%d" % (self.slot_id))

		time_before = time.time()

		relative_time = int(self.time_start - time_before)
		if relative_time < 0:
			raise Exception("Start time can't be in the past")

		self.alh.post("sensing/program",
			"in %d sec for %d sec with dev %d conf %d ch %d:%d:%d to slot %d" % (
				relative_time,
				self.time_duration,
				self.device_id,
				self.config_id,
				self.ch_start,
				self.ch_step,
				self.ch_stop,
				self.slot_id))

		time_after = time.time()

		time_error = time_after - time_before
		if time_error > self.MAX_TIME_ERROR:
			raise Exception("Programming time error %.1f s > %.1fs" % 
					(time_error, self.MAX_TIME_ERROR))

	def is_complete(self):
		if time.time() < self.time_start + self.time_duration:
			return False
		else:
			resp = self.alh.get("sensing/slotInformation", "id=%d" % (self.slot_id,))
			return "status=COMPLETE" in resp

	def _decode(self, data):
		sweep_len = len(range(self.ch_start, self.ch_stop, self.ch_step))
		line_bytes = sweep_len * 2 + 4

		sweeps = []
		sweep = Sweep()

		for n in xrange(0, len(data), 2):
			datum = data[n:n+2]
			if len(datum) != 2:
				continue

			if n % line_bytes == 0:
				# got a time-stamp
				t = data[n:n+4]
				tt = struct.unpack("<I", t)[0]
				assert not sweep.data
				sweep.timestamp = tt * 1e-3
				continue

			if n % line_bytes == 2:
				# second part of a time-stamp, just ignore
				assert not sweep.data
				continue

			dbm = struct.unpack("h", datum)[0]*1e-2
			sweep.data.append(dbm)

			if len(sweep.data) >= sweep_len:
				sweeps.append(sweep)
				sweep = Sweep()

		if(sweep.data):
			sweeps.append(sweep)

		return sweeps

	def retrieve(self):
		resp = self.alh.get("sensing/slotInformation", "id=%d" % (self.slot_id,))
		assert "status=COMPLETE" in resp

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

	def get_device_config(self):
		# get the description
		description = self.alh.get("sensing/deviceConfigList",
								"devNum=%d" % (self.device_id))
		# parse description
		lines = description.split("\n")
		# print "lines=", lines

		cfg_name_line = lines[1 + 2*self.config_id]
		# print "cfg_name_line",cfg_name_line

		cfg_re = re.compile(" *cfg #(.*): (.*):(.*)")
		cfg_matches = cfg_re.match(cfg_name_line).groups()
		# print "got1: ", cfg_matches

		assert int(cfg_matches[0]) == self.config_id
		# cfg_desc = cfg_matches[1] # unused
		# print "config_desc: ", cfg_desc

		cfg_params_line = lines[2 + 2*self.config_id]
		# print "cfg_params_line", cfg_params_line

		par_re = re.compile(" *base: (.*) Hz, spacing: (.*) Hz, bw: (.*) Hz, channels: (.*), time: (.*) ms")
		par_matches = par_re.match(cfg_params_line).groups()
		# print "got2: ", par_matches

		config = DeviceConfig(self.config_id)
		config.base = int(par_matches[0])
		config.spacing = int(par_matches[1])
		config.bw = int(par_matches[2])
		config.num = int(par_matches[3])
		config.time = int(par_matches[4])

		return config

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
	MAX_TIME_ERROR = 2.0

	def __init__(self, alh, time_start, time_duration, 
			device_id, config_id, channel, power):

		self.alh = alh

		self.time_start = time_start
		self.time_duration = time_duration
		self.device_id = device_id
		self.config_id = config_id
		self.channel = channel
		self.power = power

	def program(self):
		time_before = time.time()

		relative_time = int(self.time_start - time_before)
		if relative_time < 0:
			raise Exception("Start time can't be in the past")

		self.alh.post("generator/program",
			"in %d sec for %d sec with dev %d conf %d channel %d power %d" % (
				relative_time,
				self.time_duration,
				self.device_id,
				self.config_id,
				self.channel,
				self.power))

		time_after = time.time()

		time_error = time_after - time_before
		if time_error > self.MAX_TIME_ERROR:
			raise Exception("Programming time error %.1f s > %.1fs" % 
					(time_error, self.MAX_TIME_ERROR))

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

		config = run.get_device_config()

		if hasattr(run.alh, "addr"):
			name = "node_%d.dat" % (run.alh.addr,)
		else:
			name = "run_%d.dat" % (n,)

		fn = "%s/%s" % (path, name)
		outf = open(fn, "w")
		outf.write("# t [s]\tf [Hz]\tP [dBm]\n")

		sweep_len = len(range(run.ch_start, run.ch_stop, run.ch_step))

		sweep_time = 0.0

		next_sweep_i = iter(result)
		next_sweep_i.next()
		i = itertools.izip_longest(result, next_sweep_i)

		for sweepnr, (sweep, next_sweep) in enumerate(i):
			assert isinstance(sweep, Sweep)

			if next_sweep is not None:
				sweep_time = next_sweep.timestamp - sweep.timestamp

			for dbmn, dbm in enumerate(sweep.data):

				time = sweep.timestamp + sweep_time/sweep_len * dbmn

				channel = run.ch_start + run.ch_step * dbmn
				assert channel < run.ch_stop

				freq = config.ch_to_hz(channel)

				outf.write("%f\t%f\t%f\n" % (time, freq, dbm))

			outf.write("\n")

		outf.close()
