import binascii
try:
	from itertools import zip_longest
except ImportError:
	from itertools import izip_longest as zip_longest
import logging
import re
import struct
import time

from vesna.spectrumsensor import Device, DeviceConfig, ConfigList, SweepConfig, Sweep
from vesna.alh import CRCError, ALHException

log = logging.getLogger(__name__)

class ALHProgrammingTimeError(ALHException): pass

class SpectrumSensorProgram:
	"""Describes a single spectrum sensing task.

	:param sweep_config: frequency sweep configuration to use, a :py:class:`SweepConfig` object
	:param time_start: time to start the task (UNIX timestamp)
	:param time_duration: duration of the task in seconds
	:param slot_id: numerical slot id used for storing measurements
	"""

	def __init__(self, sweep_config, time_start, time_duration, slot_id):
		self.sweep_config = sweep_config
		self.time_start = time_start
		self.time_duration = time_duration
		self.slot_id = slot_id

class SpectrumSensorResult:
	"""Result of a spectrum sensing task."""

	def __init__(self, program):
		"""Create a new result object.

		program -- SpectrumSensorProgram object that produced these results.
		"""
		self.program = program
		self.sweeps = []

	def get_hz_list(self):
		"""Return a list of frequencies in hertz covered by this result.
		"""
		return self.program.sweep_config.get_hz_list()

	def get_s_list(self):
		"""Return a list of timestamps in seconds covered by this result.
		"""
		return [ sweep.timestamp for sweep in self.sweeps ]

	def get_data(self):
		"""Return power measurements in dbm in form a two-dimensional array.
		"""
		data = []

		row_len = len(self.program.sweep_config.get_ch_list())

		for sweep in self.sweeps:
			if len(sweep.data) == row_len:
				row = sweep.data
			else:
				# only last row can be shorter
				assert len(data) == len(self.sweeps) - 1

				row = sweep.data + [sweep.data[-1]] * (row_len - len(sweep.data))

			data.append(row)

		return data

	def write(self, path):
		"""Write measurements into a tab-separated-values file.

		:param path: path to the file to write
		"""

		outf = open(path, "w")

		outf.write("# t [s]\tf [Hz]\tP [dBm]\n")

		sweep_config = self.program.sweep_config
		num_channels = sweep_config.num_channels
		sweep_time = 0.0

		next_sweep_i = iter(self.sweeps)
		next(next_sweep_i)
		i = zip_longest(self.sweeps, next_sweep_i)

		for sweepnr, (sweep, next_sweep) in enumerate(i):
			assert isinstance(sweep, Sweep)

			if next_sweep is not None:
				sweep_time = next_sweep.timestamp - sweep.timestamp

			for dbmn, dbm in enumerate(sweep.data):

				time = sweep.timestamp + sweep_time/num_channels * dbmn

				channel = sweep_config.start_ch + sweep_config.step_ch * dbmn
				assert channel < sweep_config.stop_ch

				freq = sweep_config.config.ch_to_hz(channel)

				outf.write("%f\t%f\t%f\n" % (time, freq, dbm))

			outf.write("\n")

		outf.close()

class SpectrumSensor:
	"""ALH node acting as a spectrum sensor.

	:param alh: ALH implementation used to communicate with the node
	"""
	MAX_TIME_ERROR = 2.0
	MAX_SINGLE_SWEEP_TIME = 800e-3

	def __init__(self, alh):
		self.alh = alh

	def _split_sweep_config(self, sweep_config):

		ch_per_sweep = int(self.MAX_SINGLE_SWEEP_TIME / (sweep_config.config.time * 1e-3))

		sweep_config_list = []

		start_ch = sweep_config.start_ch
		step_ch = sweep_config.step_ch
		while start_ch < sweep_config.stop_ch:
			stop_ch = min(sweep_config.stop_ch, start_ch + ch_per_sweep * step_ch)

			sweep_config_list.append(SweepConfig(sweep_config.config, start_ch, stop_ch, step_ch))
			start_ch = stop_ch

		return sweep_config_list

	@staticmethod
	def _crc32(data):
		v= binascii.crc32(data) & 0xffffffff
		return v

	def _sweep(self, sweep_config):
		response = self.alh.post("sensing/quickSweepBin",
				"dev %d conf %d ch %d:%d:%d" % (
				sweep_config.config.device.id,
				sweep_config.config.id,
				sweep_config.start_ch,
				sweep_config.step_ch,
				sweep_config.stop_ch))

		data = response.content[:-4]
		crc = response.content[-4:]

		their_crc = struct.unpack("<I", crc[-4:])[0]
		our_crc = self._crc32(data)
		if their_crc != our_crc:
			# Firmware versions 2.29 only calculate CRC on the
			# first half of the response due to a bug
			our_crc = self._crc32(data[:len(data)//2])
			if their_crc != our_crc:
				raise CRCError
			else:
				log.warning("working around broken CRC calculation! "
						"please upgrade node firmware")

		assert sweep_config.num_channels * 2 == len(data)

		result = []
		for n in range(0, len(data), 2):
			datum = data[n:n+2]

			dbm = struct.unpack("<h", datum)[0]*1e-2
			result.append(dbm)

		return result

	def sweep(self, sweep_config):
		"""Perform a single frequency sweep and return results
		immediately

		:param sweep_config: frequency sweep configuration to use, a :py:class:`SweepConfig` object
		"""

		sweep = Sweep()
		sweep.timestamp = 0

		for sweep_config in self._split_sweep_config(sweep_config):
			data = self._sweep(sweep_config)
			sweep.data += data

		return sweep

	def program(self, program):
		"""Send the given spectrum sensing program to the node.

		:param program: a :py:class:`SpectrumSensorProgram` object
		"""

		self.alh.post("sensing/freeUpDataSlot", "1", "id=%d" % (program.slot_id))

		time_before = time.time()

		relative_time = int(program.time_start - time_before)
		if relative_time < 0:
			raise Exception("Start time can't be in the past")

		self.alh.post("sensing/program",
			"in %d sec for %d sec with dev %d conf %d ch %d:%d:%d to slot %d" % (
				relative_time,
				program.time_duration,
				program.sweep_config.config.device.id,
				program.sweep_config.config.id,
				program.sweep_config.start_ch,
				program.sweep_config.step_ch,
				program.sweep_config.stop_ch,
				program.slot_id))

		time_after = time.time()

		time_error = time_after - time_before
		if time_error > self.MAX_TIME_ERROR:
			raise ALHProgrammingTimeError("Programming time error %.1f s > %.1fs" % 
					(time_error, self.MAX_TIME_ERROR))

	def is_complete(self, program):
		"""Return true if given program has been successfuly completed.

		:param program: a :py:class:`SpectrumSensorProgram` object
		"""
		if time.time() < program.time_start + program.time_duration:
			return False
		else:
			resp = self.alh.get("sensing/slotInformation", "id=%d" % (program.slot_id,))
			return "status=COMPLETE" in resp.decode("UTF-8")

	@staticmethod
	def _decode(program, data):
		num_channels = program.sweep_config.num_channels
		line_bytes = num_channels * 2 + 4

		result = SpectrumSensorResult(program)

		sweep = Sweep()
		for n in range(0, len(data), 2):
			datum = data[n:n+2]
			if len(datum) != 2:
				continue

			if n % line_bytes == 0:
				# got a time-stamp
				t = data[n:n+4]
				tt = struct.unpack("<i", t)[0]
				assert not sweep.data
				sweep.timestamp = tt * 1e-3
				continue

			if n % line_bytes == 2:
				# second part of a time-stamp, just ignore
				assert not sweep.data
				continue

			dbm = struct.unpack("<h", datum)[0]*1e-2
			sweep.data.append(dbm)

			if len(sweep.data) >= num_channels:
				result.sweeps.append(sweep)
				sweep = Sweep()

		if(sweep.data):
			result.sweeps.append(sweep)

		return result

	def retrieve(self, program):
		"""Retrieve results from the given spectrum sensing program.

		:param program: a :py:class:`SpectrumSensorProgram` object
		:return: a :py:class:`SpectrumSensorResult` object
		"""
		resp = self.alh.get("sensing/slotInformation", "id=%d" % (program.slot_id,))

		assert "status=COMPLETE" in resp.text

		g = re.search("size=([0-9]+)", resp.text)
		total_size = int(g.group(1))

		#print "total size:", total_size

		p = 0
		max_read_size = 512
		data = b""

		while p < total_size:
			chunk_size = min(max_read_size, total_size - p)

			#if p < total_size - chunk_size*2:
			#	p += max_read_size
			#	continue

			#print "start", p
			#print "size", chunk_size

			chunk_data_crc = self.alh.get("sensing/slotDataBinary", "id=%d&start=%d&size=%d" % (
				program.slot_id, p, chunk_size))

			chunk_data = chunk_data_crc.content[:-4]

			#print "len", len(chunk_data)
			
			their_crc = struct.unpack("I", chunk_data_crc.content[-4:])[0]
			our_crc = self._crc32(chunk_data)

			if(their_crc != our_crc):
				raise CRCError

			data += chunk_data

			p += max_read_size

		return self._decode(program, data)

	def get_config_list(self):
		"""Query and return the list of supported device configurations.

		:return: a :py:class:`ConfigList` object
		"""
		config_list = ConfigList()

		device = None
		config = None

		description = self.alh.get("sensing/deviceConfigList")
		description = description.decode("ascii")
		configs_left = 0
		state = 0
		for line in description.split("\n"):
			g = re.match("dev #([0-9]+), (.+), ([0-9]+) configs:", line)
			if state == 0 and g:
				device = Device(int(g.group(1)), g.group(2))
				config_list._add_device(device)
				configs_left = int(g.group(3))
				state = 1
				continue

			g = re.match("  cfg #([0-9]+): (.+):", line)
			if state == 1 and g:
				config = DeviceConfig(int(g.group(1)), g.group(2), device)
				state = 2

				continue

			g = re.match("     base: ([0-9]+) Hz, spacing: ([0-9]+) Hz, bw: ([0-9]+) Hz, channels: ([0-9]+), time: ([0-9]+) ms", line)
			if state == 2 and g:
				config.base = int(g.group(1))
				config.spacing = int(g.group(2))
				config.bw = int(g.group(3))
				config.num = int(g.group(4))
				config.time = int(g.group(5))

				config_list._add_config(config)

				configs_left -= 1
				if configs_left < 0:
					raise CRCError
				elif configs_left == 0:
					state = 0
				else:
					state = 1

				continue

		if configs_left != 0:
			raise CRCError

		return config_list
