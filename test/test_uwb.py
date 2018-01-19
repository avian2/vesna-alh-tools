import unittest
from vesna.alh.uwbnode import RadioSettings

class TestRadioSettings(unittest.TestCase):
	def test_get_dict(self):
		settings = RadioSettings()

		settings.channel = 5
		settings.channel_code = 9
		settings.prf = 64
		settings.datarate = 110
		settings.preamble_length = 1024
		settings.pac_size = 32
		settings.nssfd = 1
		settings.sfd_timeout = 1024 + 32 + 1

		self.assertEqual({'ch': 5, 'ch_code': 9, 'prf': 64, 'dr': 110, 'plen': 1024, 'pac': 32, 'nssfd': 1, 'sfdto': 1057}, settings.get_dict())
