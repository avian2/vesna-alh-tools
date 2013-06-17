import unittest

from vesna.alh import signalgenerator

class TestGeneratorConfigList(unittest.TestCase):
	def test_get_config_name(self):
		cl = signalgenerator.ConfigList()

		d = signalgenerator.Device(0, "test")
		cl._add_device(d)

		def add_dc(id, name, base):
			dc = signalgenerator.DeviceConfig(id, name, d)
			dc.base = base 
			dc.spacing = 1
			dc.num = 1000
			dc.time = 1
			dc.min_power = -100
			dc.max_power = 0
			cl._add_config(dc)

		add_dc(0, "foo 1", 1000)
		add_dc(1, "foo 2", 2000)
		add_dc(2, "bar 1", 1000)
		add_dc(3, "bar 2", 2000)

		sc = cl.get_tx_config(1500, 0)
		self.assertEquals(0, sc.config.id)

		sc = cl.get_tx_config(2500, 0)
		self.assertEquals(1, sc.config.id)

		sc = cl.get_tx_config(1500, 0, name="bar")
		self.assertEquals(2, sc.config.id)

		sc = cl.get_tx_config(2500, 0, name="bar")
		self.assertEquals(3, sc.config.id)

from vesna.alh.spectrumsensor import SpectrumSensorResult, SpectrumSensorProgram
from vesna.spectrumsensor import Device, DeviceConfig, SweepConfig, Sweep

class TestSpectrumSensorResult(unittest.TestCase):
	def setUp(self):
		d = Device(0, "test")

		dc = DeviceConfig(0, "foo", d)
		dc.base = 1000
		dc.spacing = 1
		dc.num = 1000

		sc = SweepConfig(dc, 0, 3, 1)

		p = SpectrumSensorProgram(sc, 0, 10, 1)

		self.r = r = SpectrumSensorResult(p)

		s = Sweep()
		s.timestamp = 0.0
		s.data = [ 0.0, 1.0, 2.0 ]
		r.sweeps.append(s)

		s = Sweep()
		s.timestamp = 1.0
		s.data = [ 3.0, 4.0 ]
		r.sweeps.append(s)

	def test_get_data(self):
		self.assertEqual( [
			[ 0.0, 1.0, 2.0 ],
			[ 3.0, 4.0, 4.0 ]
		], self.r.get_data())

	def test_get_hz_list(self):
		self.assertEqual( [ 1000.0, 1001.0, 1002.0 ], self.r.get_hz_list() )

	def test_get_s_list(self):
		self.assertEqual( [ 0.0, 1.0 ], self.r.get_s_list() )
