import math
import time

from vesna.alh import ALHProxy
from vesna.alh.common import add_communication_options, get_coordinator
from vesna.alh.spectrumsensor import SpectrumSensor, SpectrumSensorProgram, SweepConfig
from vesna.rftest import DeviceUnderTest

class RemoteDeviceUnderTest(DeviceUnderTest):
	def add_options(self, parser):
		add_communication_options(parser)

		parser.add_option("-n", "--node", dest="node", metavar="ADDR", type="int",
				help="Connect to node with ZigBit address ADDR")

	def setup(self, options):

		if not options.verbosity:
			options.verbosity = "warning"

		coor = get_coordinator(options)
		coor.post("prog/firstcall", "1")

		self.node = ALHProxy(coor, options.node)
		self.node.post("prog/firstcall", "1")

		self.spectrumsensor = SpectrumSensor(self.node)

		self.config_list = self.spectrumsensor.get_config_list()
		if not self.config_list.configs:
			raise Exception("Device returned no configurations. "
					"It is still scanning or not responding.")

		self.config = self.config_list.get_config(self.device_id, self.config_id)

	def get_fw_version(self):
		return self.node.get("hello").strip()

	def get_status(self):
		resp = self.node.get("sensing/deviceStatus").strip()
		return [v.strip() for v in resp.split("\n") ]

	def measure_ch_impl(self, ch, n):
		sweep_config = SweepConfig(self.config, ch, ch+1, 1)

		duration = int(math.ceil(self.config.time * n * 1e-3 + 1.0))

		now = time.time()
		sensor_program = SpectrumSensorProgram(sweep_config, now + 1, duration, 2)

		self.spectrumsensor.program(sensor_program)
		while not self.spectrumsensor.is_complete(sensor_program):
			time.sleep(1)

		result = self.spectrumsensor.retrieve(sensor_program)

		measurements = [ sweep.data[0] for sweep in result.sweeps ]
		measurements = measurements[:n]

		assert len(measurements) == n
		return measurements


