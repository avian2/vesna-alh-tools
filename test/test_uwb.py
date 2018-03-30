import struct
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

from vesna.alh.uwbnode import parseCIR2Complex
from vesna.alh.uwbnode import dataLineToDictionary

class TestUWB(unittest.TestCase):
	def test_parsecir2complex_zeros(self):
		data = '\x00\x00\x00\x00'
		c = parseCIR2Complex(data)

		self.assertEqual(c, ['0j'])

	def test_parsecir2complex_examples(self):

		def test(a, b):
			data = struct.pack(">hh", a, b)

			c = parseCIR2Complex(data)

			self.assertEqual(c, ['(%d%+dj)' % (a,b)] )

		test(1,1)
		test(256,256)
		test(-1,-1)
		test(-512,-512)
		test(-1024,-512)

	def test_datalinetodictionary(self):

		line = """SRC:testtesttesttest
DEST:testtesttesttest
DIST:001.5
FP_INDEX:002
FP_AMPL1:00001
FP_AMPL2:00000
FP_AMPL3:00000
CIR_PWR:00000
PRFR:00
RXPACC:00001
STD_NOISE:00000
MAX_NOISE:00004
"""

		msg_dict = dataLineToDictionary(line)

		self.assertEqual(msg_dict, {
			'cir': None,
			'dest_id': 'testtesttesttest',
			'fp_index': 2,
			'max_noise': 4,
			'node_id': 'testtesttesttest',
			'noise_stdev': 0,
			'range': 1.5,
			'rss': -121.74,
			'rss_fp': -121.74,
			'rxpacc': 1
		})
