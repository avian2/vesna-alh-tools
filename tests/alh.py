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
