import unittest

try:
	from StringIO import StringIO as BytesIO
except ImportError:
	from io import BytesIO

import datetime

import vesna.cdf
import vesna.cdf.xml

class TestCDFMetadata(unittest.TestCase):
	def test_empty(self):
		obj2 = vesna.cdf.xml._metadata_decode("")

		self.assertEqual(obj2, None)

	def test_basic(self):
		obj = ['foo']

		b = vesna.cdf.xml._metadata_encode(obj)
		obj2 = vesna.cdf.xml._metadata_decode(b)

		self.assertEqual(obj, obj2)

	def test_preserve(self):
		old_str = "hello, world!"

		obj = ['foo']

		b = vesna.cdf.xml._metadata_encode(obj, old_str)
		obj2 = vesna.cdf.xml._metadata_decode(b)

		self.assertEqual(obj, obj2)
		self.assertTrue(b.startswith(old_str))

		obj = ['bar']

		b = vesna.cdf.xml._metadata_encode(obj, b)
		obj2 = vesna.cdf.xml._metadata_decode(b)

		self.assertEqual(obj, obj2)
		self.assertTrue(b.startswith(old_str))

class TestCDFXMLExperiment(unittest.TestCase):
	def xest_create_save_load(self):
		e = vesna.cdf.CDFExperiment(title="test experiment", summary="test experiment",
				start_hz=1, stop_hz=10, step_hz=1)
		
		d = vesna.cdf.CDFDevice("http://localhost", 10000, 1)
		e.add_device(d)

		f = StringIO()
		e.save(f)

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

class TestCDFExperiment(unittest.TestCase):
	def test_create_iteration(self):
		i = vesna.cdf.CDFExperimentIteration()

	def create_experiment(self):

		e = vesna.cdf.CDFExperiment(
				title="Test experiment",
				summary="Experiment summary",
				release_date=datetime.datetime.now(),
				methodology="Collection methodology",
				related_experiments="Related experiments",
				notes="Notes")

		a = vesna.cdf.CDFAuthor(
				name="John",
				email="john@example.com",
				address="Nowhere",
				phone="0",
				institution="Institute of Imaginary Science")
		e.add_author(a)

		d = vesna.cdf.CDFDocument(
				description="A document",
				bibtex="BibTeX")
		e.add_document(d)

		e.set_frequency_range(
				start_hz=100e6,
				stop_hz=200e6,
				step_hz=1e6)

		e.set_duration(60)

		d = vesna.cdf.CDFDevice(
				base_url="http://example.com/communicator", 
				cluster_id=10000, 
				addr=1)

		e.add_device(d)

		d = vesna.cdf.CDFDevice(
				base_url="http://example.com/communicator", 
				cluster_id=10000, 
				addr=2)

		i = vesna.cdf.CDFInterferer(
				device=d)

		p = vesna.cdf.CDFInterfererProgram(
				center_hz=150e6,
				power_dbm=0,

				device_id=0,
				config_id=0,

				start_time=10,
				end_time=20)

		i.add_program(p)

		e.add_interferer(i)

		return e

	def test_create(self):
		self.create_experiment()

	def test_xml_create(self):
		e = self.create_experiment()
		vesna.cdf.xml.CDFXMLExperiment(e)

	def test_xml_save_load(self):
		io = BytesIO()

		e = self.create_experiment()
		e = vesna.cdf.xml.CDFXMLExperiment(e)
		e.save(io)

		#print io.getvalue()

		io.seek(0)

		e2 = vesna.cdf.xml.CDFXMLExperiment.load(io)

		self.assertEqual(e.get_experiment().title, e2.get_experiment().title)
