import itertools
import re
import time

from vesna.alh import CRCError

class Device:
	"""A signal generation device.

	A particular hardware model can have one or more physical signal generation devices, each of which
	can support one or more configurations.
	"""
	def __init__(self, id, name):
		"""Create a new device.

		id -- numeric device id.
		name -- string with a human readable name of the device.
		"""
		self.id = id
		self.name = name

class DeviceConfig: 
	"""Configuration for a signal generation device.

	The set of possible configurations for a device is usually hardware-dependent (i.e. a
	configuration usually reflects physical hardware settings). A configuration defines the usable
	frequency and power range.
	"""
	def __init__(self, id, name, device):
		"""Create a new device configuration.

		id -- numeric configuration id.
		name -- string with a human readable name of the configuration.
		device -- Device object to which this configuration applies.
		"""
		self.id = id
		self.name = name
		self.device = device

	def ch_to_hz(self, ch):
		"""Convert channel number to center frequency in hertz."""
		assert ch >= 0
		assert ch < self.num

		return self.base + self.spacing * ch

	def get_start_hz(self):
		"""Return the lowest settable frequency."""
		return self.ch_to_hz(0)

	def get_stop_hz(self):
		"""Return the highest settable frequency."""
		return self.ch_to_hz(self.num - 1)

	def covers(self, f_hz, power_dbm):
		"""Return true if this configuration can support the given frequency and power.

		:param f_hz: transmission frequency in hertz
		:param power_dbm: transmission power in dBm
		"""
		return f_hz >= self.get_start_hz() and f_hz <= self.get_stop_hz() and \
				power_dbm >= self.min_power and power_dbm <= self.max_power

	def get_tx_config(self, f_hz, power_dbm):
		"""Return the transmission configuration for the given frequency and power.

		:param f_hz: transmission frequency in hertz
		:param power_dbm: transmission power in dBm
		"""
		assert self.covers(f_hz, power_dbm)

		f_ch = int(round((f_hz - self.base) / self.spacing))

		return TxConfig(self, f_ch, power_dbm)

	def __str__(self):
		return "channel config %d,%d: %10d - %10d Hz" % (
				self.device.id, self.id, self.get_start_hz(), self.get_stop_hz())

class TxConfig:
	"""Transmission configuration for a signal generation device.

	:param config: :py:class:`DeviceConfig` device configuration object to use
	:param f_ch: frequency channel for transmission
	:param power_db: power level for transmission
	"""

	def __init__(self, config, f_ch, power_dbm):
		assert f_ch >= 0
		assert f_ch < config.num
		assert power_dbm >= config.min_power
		assert power_dbm <= config.max_power

		self.config = config
		self.f_ch = f_ch
		self.power_dbm = power_dbm

class ConfigList:
	"""List of devices and device configurations supported by attached hardware."""

	def __init__(self):
		"""Create a new list."""
		self.configs = []
		self.devices = []

	def _add_device(self, device):
		self.devices.append(device)

	def _add_config(self, config):
		self.configs.append(config)

	def get_config(self, device_id, config_id):
		"""Return the specified device configuration.

		:param device_id: numeric device id, as returned by the `list` command
		:param config_id: numeric configuration id, as returned by the `list` command
		"""
		for config in self.configs:
			if config.id == config_id and config.device.id == device_id:
				return config

		return None

	def get_tx_config(self, f_hz, power_dbm, name=None):
		"""Return best transmission configuration for specified requirements.

		:param f_hz: transmission frequency
		:param power_dbm: transmission power
		:param name: optional required sub-string in device configuration name
		"""

		candidates = []

		for config in self.configs:
			if name and name not in config.name:
				continue

			if not config.covers(f_hz, power_dbm):
				continue

			candidates.append(config)

		# pick fastest matching config
		candidates.sort(key=lambda x:x.time, reverse=True)

		if candidates:
			return candidates[0].get_tx_config(f_hz, power_dbm)
		else:
			return None

	def __str__(self):
		lines = []
		for device in self.devices:
			lines.append("device %d: %s" % (device.id, device.name))
			for config in self.configs:
				if config.device is device:
					lines.append("  channel config %d,%d: %s" % (device.id, config.id, config.name))
					lines.append("    base: %d Hz" % (config.base,))
					lines.append("    spacing: %d Hz" % (config.spacing,))
					lines.append("    bw: %d Hz" % (config.bw,))
					lines.append("    num: %d" % (config.num,))
					lines.append("    power: %d ... %d dBm" % (config.min_power, config.max_power))
					lines.append("    time: %d ms" % (config.time,))

		return '\n'.join(lines)

class SignalGeneratorProgram:
	"""Describes a single signal generation task.

	:param tx_config: transmission configuration to use
	:param time_start: time to start the task (UNIX timestamp)
	:param time_duration: duration of the task in seconds
	"""

	def __init__(self, tx_config, time_start, time_duration):
		self.tx_config = tx_config
		self.time_start = time_start
		self.time_duration = time_duration

class SignalGenerator:
	"""ALH node acting as a signal generator.

	:param alh: ALH implementation used to communicate with the node
	"""
	MAX_TIME_ERROR = 2.0

	def __init__(self, alh):
		self.alh = alh

	def program(self, program):
		"""Send the given signal generation program to the node.

		:param program: a :py:class:`SignalGeneratorProgram` object
		"""
		return self.program_list([program])

	def program_list(self, program_list):
		"""Send several signal generator programs to the node.

		:param program_list: a list of :py:class:`SignalGeneratorProgram` objects
		"""
		time_before = time.time()

		data_list = []

		for program in program_list:

			relative_time = int(program.time_start - time_before)
			if relative_time < 0:
				raise Exception("Start time can't be in the past")

			data_list.append("in %d sec for %d sec with dev %d conf %d channel %d power %d" % (
					relative_time,
					program.time_duration,
					program.tx_config.config.device.id,
					program.tx_config.config.id,
					program.tx_config.f_ch,
					program.tx_config.power_dbm))

		self.alh.post("generator/program", "\n".join(data_list))

		time_after = time.time()

		time_error = time_after - time_before
		if time_error > self.MAX_TIME_ERROR:
			raise Exception("Programming time error %.1f s > %.1fs" % 
					(time_error, self.MAX_TIME_ERROR))

	def get_config_list(self):
		"""Query and return the list of supported device configurations.

		:return: a :py:class:`ConfigList` object
		"""
		config_list = ConfigList()

		device = None
		config = None

		description = self.alh.get("generator/deviceConfigList")
		description_ascii = description.decode('ascii')
		configs_left = 0
		state = 0
		for line in description_ascii.split("\n"):
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

			g = re.match("     base: ([0-9]+) Hz, spacing: ([0-9]+) Hz, bw: ([0-9]+) Hz, channels: ([0-9]+), min power: ([0-9-]+) dBm, max power: ([0-9-]+) dBm, time: ([0-9]+) ms", line)
			if state == 2 and g:
				config.base = int(g.group(1))
				config.spacing = int(g.group(2))
				config.bw = int(g.group(3))
				config.num = int(g.group(4))
				config.min_power = int(g.group(5))
				config.max_power = int(g.group(6))
				config.time = int(g.group(7))

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
