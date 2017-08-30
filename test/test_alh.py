import unittest

from vesna.alh import CRCError
from vesna.alh import signalgenerator
from vesna.alh import cast_args_to_bytes

#import logging
#logging.basicConfig(level=logging.DEBUG)

class TestMisc(unittest.TestCase):
	def test_cast_args(self):
		class Test:
			@cast_args_to_bytes
			def get(self2, resource):
				self.assertIsInstance(resource, bytes)

		t = Test()
		t.get('test')
		t.get(b'test')
		t.get(u'test')

class TestSignalGenerator(unittest.TestCase):

	def test_get_config_list(self):

		class TestALH:
			def get(self, resource):
				s = "dev #0, Test, 1 configs:\n" \
					"  cfg #0: Test:\n" \
					"     base: 10 Hz, spacing: 1 Hz, bw: 1 Hz, channels: 10, min power: -10 dBm, max power: 0 dBm, time: 1 ms"
				return s.encode('ascii')

		alh = TestALH()
		s = signalgenerator.SignalGenerator(alh)

		cl = s.get_config_list()

		self.assertEqual(len(cl.devices), 1)
		self.assertEqual(len(cl.configs), 1)

	def test_get_config_list_corrupt_1(self):

		class TestALH:
			def get(self, resource):
				return b""

		alh = TestALH()
		s = signalgenerator.SignalGenerator(alh)

		cl = s.get_config_list()

		self.assertEqual(cl.configs, [])
		self.assertEqual(cl.devices, [])

	def test_get_config_list_corrupt_2(self):

		class TestALH:
			def get(self, resource):
				return b"dev #0, Test, 2 configs:"

		alh = TestALH()
		s = signalgenerator.SignalGenerator(alh)

		self.assertRaises(CRCError, s.get_config_list)

	def test_get_config_list_corrupt_3(self):

		class TestALH:
			def get(self, resource):
				s = "dev #0, Test, 1 configs:\n"\
					"  cfg #0: Test:"
				return s.encode('ascii')

		alh = TestALH()
		s = signalgenerator.SignalGenerator(alh)

		self.assertRaises(CRCError, s.get_config_list)


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
		self.assertEqual(0, sc.config.id)

		sc = cl.get_tx_config(2500, 0)
		self.assertEqual(1, sc.config.id)

		sc = cl.get_tx_config(1500, 0, name="bar")
		self.assertEqual(2, sc.config.id)

		sc = cl.get_tx_config(2500, 0, name="bar")
		self.assertEqual(3, sc.config.id)

from vesna.alh.spectrumsensor import SpectrumSensor, SpectrumSensorResult, SpectrumSensorProgram
from vesna.spectrumsensor import Device, DeviceConfig, SweepConfig, Sweep

class TestSpectrumSensor(unittest.TestCase):

	def test_get_config_list(self):

		class TestALH:
			def get(self, resource):
				s =	"dev #0, Test, 1 configs:\n" \
					"  cfg #0: Test:\n" \
					"     base: 10 Hz, spacing: 1 Hz, bw: 1 Hz, channels: 10, time: 1 ms"
				return s.encode('ascii')

		alh = TestALH()
		s = SpectrumSensor(alh)

		cl = s.get_config_list()

		self.assertEqual(len(cl.devices), 1)
		self.assertEqual(len(cl.configs), 1)

	def test_get_config_list_corrupt_1(self):

		class TestALH:
			def get(self, resource):
				return "".encode('ascii')

		alh = TestALH()
		s = SpectrumSensor(alh)

		cl = s.get_config_list()

		self.assertEqual(cl.configs, [])
		self.assertEqual(cl.devices, [])

	def test_get_config_list_corrupt_2(self):

		class TestALH:
			def get(self, resource):
				s = "dev #0, Test, 2 configs:"
				return s.encode('ascii')

		alh = TestALH()
		s = SpectrumSensor(alh)

		self.assertRaises(CRCError, s.get_config_list)

	def test_get_config_list_corrupt_3(self):

		class TestALH:
			def get(self, resource):
				s = "dev #0, Test, 1 configs:\n"\
					"  cfg #0: Test:"
				return s.encode('ascii')

		alh = TestALH()
		s = SpectrumSensor(alh)

		self.assertRaises(CRCError, s.get_config_list)

	def _get_sc(self):
		d = Device(0, "test")

		dc = DeviceConfig(0, "foo", d)
		dc.base = 1000
		dc.spacing = 1
		dc.num = 1000
		dc.time = 1

		sc = SweepConfig(dc, 0, 3, 1)

		return sc

	def test_sweep_1(self):
		class MockALH(ALHProtocol):
			def _post(self, resource, data, *args):
				return b"\x00\x00\x01\x00\x02\x00D\xa4H;"

		alh = MockALH()
		ss = SpectrumSensor(alh)

		sc = self._get_sc()
		r = ss.sweep(sc)

		self.assertEqual(r.data, [0., .01, .02])

	def test_sweep_2(self):
		class MockALH(ALHProtocol):
			def _post(self, resource, data, *args):
				# negative CRC
				return b"\x00\x00\x01\x00\x08\x00\xceL\xa7\xc1"

		alh = MockALH()
		ss = SpectrumSensor(alh)

		sc = self._get_sc()
		r = ss.sweep(sc)

		self.assertEqual(r.data, [0., .01, .08])

	def test_retrieve(self):
		class MockALH(ALHProtocol):
			def _get(self, resource, *args):
				if b"Info" in resource:
					return b"status=COMPLETE,size=14"
				else:
					return b"\x00\x00\x00\x00\x00\x00\x01\x00\x02\x00\x91m\x00i"

		alh = MockALH()
		ss = SpectrumSensor(alh)

		sc = self._get_sc()
		p = SpectrumSensorProgram(sc, 0, 10, 1)

		r = ss.retrieve(p)

		self.assertEqual(len(r.sweeps), 1)
		self.assertEqual(r.sweeps[0].data, [0., .01, .02])
		self.assertEqual(r.sweeps[0].timestamp, 0)

import tempfile

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

	def test_write(self):
		f = tempfile.NamedTemporaryFile()

		self.r.write(f.name)

		f.seek(0)
		a = f.read()

		self.assertEqual(a, b"""# t [s]	f [Hz]	P [dBm]
0.000000	1000.000000	0.000000
0.333333	1001.000000	1.000000
0.666667	1002.000000	2.000000

1.000000	1000.000000	3.000000
1.333333	1001.000000	4.000000

""")

from vesna.alh import ALHProtocol

class TestALHProtocol(unittest.TestCase):
	def test_is_printable_1(self):
		self.assertEqual(ALHProtocol._is_printable("foo".encode('ascii')), True)

	def test_is_printable_2(self):
		self.assertEqual(ALHProtocol._is_printable("\x00".encode('ascii')), False)

	def test_is_printable_3(self):
		self.assertEqual(ALHProtocol._is_printable(u"\x8f".encode('latin2')), False)

try:
	from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except ImportError:
	from http.server import HTTPServer, BaseHTTPRequestHandler

import threading
from vesna.alh import ALHWeb

class TestALHWeb(unittest.TestCase):
	def setUp(self):

		self.last_path = last_path = [None]
		self.last_headers = last_headers = [None]
		self.srv_response = srv_response = [None]

		class MockHTTPRequestHandler(BaseHTTPRequestHandler):
			def do_GET(self):
				last_path[0] = self.path
				last_headers[0] = self.headers

				self.send_response(200)
				self.end_headers()

				self.wfile.write(srv_response[0])

			def log_message(self, format, *args):
				pass

		server_address = ('localhost', 12345)
		self.httpd = HTTPServer(server_address, MockHTTPRequestHandler)
		self.t = threading.Thread(target=self.httpd.serve_forever)
		self.t.start()

	def tearDown(self):
		self.httpd.shutdown()
		self.t.join()
		self.httpd.server_close()

	def test_get_ascii(self):
		self.srv_response[0] = 'bar'.encode('ascii')

		alh = ALHWeb("http://localhost:12345", "id")
		r = alh.get("foo")

		self.assertEqual(r.text, 'bar')
		self.assertEqual('/?method=get&resource=foo%3F&cluster=id', self.last_path[0])
		self.assertIn('alh', self.last_headers[0]['User-Agent'])

	def test_get_bin(self):
		self.srv_response[0] = b'\x00\x01\x02\x04\xfe\xff'

		alh = ALHWeb("http://localhost:12345", "id")
		r = alh.get("foo")

		self.assertEqual(r.content, self.srv_response[0])

from vesna.alh import ALHTerminal

class TestALHTerminal(unittest.TestCase):
	def setUp(self):

		class MockSerial(object):
			def __init__(self):
				self.writes = []
				self.reads = []

			def read(self):
				r = self.reads[0]
				self.reads = self.reads[1:]

				return r

			def write(self, d):
				assert isinstance(d, bytes)
				self.writes.append(d)

		self.serial = MockSerial()
		self.alh = ALHTerminal(self.serial)

	def test_get_ascii(self):
		self.serial.reads.append(b"bar\r\nOK\r\n")

		r = self.alh.get("foo", "arg1")
		self.assertEqual(r.text, "bar")

		self.assertEqual(self.serial.writes, [b"get foo?arg1\r\n"])

	def test_post_ascii(self):
		self.serial.reads.append(b"bar\r\nOK\r\n")

		r = self.alh.post("foo", "datadata", "arg1")
		self.assertEqual(r.text, "bar")

		self.assertEqual(self.serial.writes,
				[b"post foo?arg1\r\nlength=8\r\ndatadata\r\ncrc=417676333\r\n"])

	def test_post_ascii_retry(self):
		self.serial.reads.append(b"CORRUPTED-DATA\r\n\r\nOK\r\n")
		self.serial.reads.append(b"bar\r\nOK\r\n")

		r = self.alh.post("foo", "datadata", "arg1")
		self.assertEqual(r.text, "bar")

		self.assertEqual(self.serial.writes,
				[b"post foo?arg1\r\nlength=8\r\ndatadata\r\ncrc=417676333\r\n",
				 b"post foo?arg1\r\nlength=8\r\ndatadata\r\ncrc=417676333\r\n"])

	def test_post_ascii_recover(self):
		self.serial.reads.append(b"JUNK-INPUT\r\n\r\nOK\r\n")
		self.serial.reads.append(b"\r\nOK\r\n")
		self.serial.reads.append(b"bar\r\nOK\r\n")

		r = self.alh.post("foo", "datadata", "arg1")
		self.assertEqual(r.text, "bar")

		self.assertEqual(self.serial.writes,
				[b"post foo?arg1\r\nlength=8\r\ndatadata\r\ncrc=417676333\r\n",
				 b"\r\n\r\n\r\n\r\n\r\n",
				 b"post foo?arg1\r\nlength=8\r\ndatadata\r\ncrc=417676333\r\n"])
