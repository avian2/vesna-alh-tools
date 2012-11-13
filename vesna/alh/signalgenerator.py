import alh
import itertools
import re
import time

from vesna.spectrumsensor import Device, DeviceConfig, ConfigList, SweepConfig, Sweep

class Device:
	def __init__(self, id, name):
		self.id = id
		self.name = name

class DeviceConfig: 
	def __init__(self, id, name, device):
		self.id = id
		self.name = name
		self.device = device

	def ch_to_hz(self, ch):
		return self.base + self.spacing * ch

	def get_start_hz(self):
		return self.ch_to_hz(0)

	def get_stop_hz(self):
		return self.ch_to_hz(self.num - 1)

	def covers(self, f_hz, power_dbm):
		"""Return true if this configuration can cover the given band
		"""
		return f_hz >= self.get_start_hz() and f_hz <= self.get_stop_hz() and \
				power_dbm >= self.min_power and power_dbm <= self.max_power

	def get_tx_config(self, f_hz, power_dbm):
		assert self.covers(f_hz, power_dbm)

		f_ch = int(round((f_hz - self.base) / self.spacing))

		return TxConfig(self, f_ch, power_dbm)

	def __str__(self):
		return "channel config %d,%d: %10d - %10d Hz" % (
				self.device.id, self.id, self.get_start_hz(), self.get_stop_hz())

class TxConfig:
	def __init__(self, config, f_ch, power_dbm):
		assert f_ch >= 0
		assert f_ch < config.num
		assert power_dbm >= config.min_power
		assert power_dbm <= config.max_power

		self.config = config
		self.f_ch = f_ch
		self.power_dbm = power_dbm

class ConfigList:
	def __init__(self):
		self.configs = []
		self.devices = []

	def _add_device(self, device):
		self.devices.append(device)

	def _add_config(self, config):
		self.configs.append(config)

	def get_config(self, device_id, config_id):
		for config in self.configs:
			if config.id == config_id and config.device.id == device_id:
				return config

		return None

	def get_tx_config(self, f_hz, power_dbm):

		candidates = []

		for config in self.configs:
			if config.covers(f_hz, power_dbm):
				candidates.append(config)

		# pick fastest matching config
		candidates.sort(key=lambda x:x.time, reverse=True)

		if candidates:
			return candidates[0].get_tx_config(f_hz, power_dbm)
		else:
			return None

class SignalGeneratorProgram:
	def __init__(self, tx_config, time_start, time_duration):
		self.tx_config = tx_config
		self.time_start = time_start
		self.time_duration = time_duration

class SignalGenerator:
	MAX_TIME_ERROR = 2.0

	def __init__(self, alh):
		self.alh = alh

	def program(self, program):
		time_before = time.time()

		relative_time = int(program.time_start - time_before)
		if relative_time < 0:
			raise Exception("Start time can't be in the past")

		self.alh.post("generator/program",
			"in %d sec for %d sec with dev %d conf %d channel %d power %d" % (
				relative_time,
				program.time_duration,
				program.tx_config.config.device.id,
				program.tx_config.config.id,
				program.tx_config.f_ch,
				program.tx_config.power_dbm))

		time_after = time.time()

		time_error = time_after - time_before
		if time_error > self.MAX_TIME_ERROR:
			raise Exception("Programming time error %.1f s > %.1fs" % 
					(time_error, self.MAX_TIME_ERROR))

	def get_config_list(self):
		config_list = ConfigList()

		device = None
		config = None

		description = self.alh.get("generator/deviceConfigList")
		for line in description.split("\n"):
			g = re.match("dev #([0-9]+), (.+), [0-9]+ configs:", line)
			if g:
				device = Device(int(g.group(1)), g.group(2))
				config_list._add_device(device)
				continue

			g = re.match("  cfg #([0-9]+): (.+):", line)
			if g:
				config = DeviceConfig(int(g.group(1)), g.group(2), device)
				config_list._add_config(config)
				continue

			g = re.match("     base: ([0-9]+) Hz, spacing: ([0-9]+) Hz, bw: ([0-9]+) Hz, channels: ([0-9]+), min power: ([0-9-]+) dBm, max power: ([0-9-]+) dBm, time: ([0-9]+) ms", line)
			if g:
				config.base = int(g.group(1))
				config.spacing = int(g.group(2))
				config.bw = int(g.group(3))
				config.num = int(g.group(4))
				config.min_power = int(g.group(5))
				config.max_power = int(g.group(6))
				config.time = int(g.group(7))
				continue

		return config_list
