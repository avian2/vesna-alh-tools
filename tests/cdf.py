import unittest
import StringIO

import vesna.cdf

class TestCDFMetadata(unittest.TestCase):
	def test_empty(self):
		obj2 = vesna.cdf._metadata_decode("")

		self.assertEqual(obj2, None)

	def test_basic(self):
		obj = ['foo']

		b = vesna.cdf._metadata_encode(obj)
		obj2 = vesna.cdf._metadata_decode(b)

		self.assertEqual(obj, obj2)

	def test_preserve(self):
		old_str = "hello, world!"

		obj = ['foo']

		b = vesna.cdf._metadata_encode(obj, old_str)
		obj2 = vesna.cdf._metadata_decode(b)

		self.assertEqual(obj, obj2)
		self.assertTrue(b.startswith(old_str))

		obj = ['bar']

		b = vesna.cdf._metadata_encode(obj, b)
		obj2 = vesna.cdf._metadata_decode(b)

		self.assertEqual(obj, obj2)
		self.assertTrue(b.startswith(old_str))

class TestCDFExperiment(unittest.TestCase):
	def test_create_save_load(self):
		e = vesna.cdf.CDFExperiment(title="test experiment", summary="test experiment",
				start_hz=1, stop_hz=10, step_hz=1)
		
		d = vesna.cdf.CDFDevice("http://localhost", 10000, 1)
		e.add_device(d)

		f = StringIO.StringIO()
		e.save(f)

		print f.getvalue()

		f.seek(0)
		e2 = vesna.cdf.CDFExperiment.load(f)

		self.assertEqual(e.title, e2.title)
		self.assertEqual(e.summary, e2.summary)
		self.assertEqual(e.start_hz, e2.start_hz)
		self.assertEqual(e.stop_hz, e2.stop_hz)
		self.assertEqual(e.step_hz, e2.step_hz)
		self.assertEqual(e.tag, e2.tag)

		self.assertEqual(e.devices[0].base_url, e2.devices[0].base_url)
		self.assertEqual(e.devices[0].cluster_id, e2.devices[0].cluster_id)
		self.assertEqual(e.devices[0].addr, e2.devices[0].addr)
