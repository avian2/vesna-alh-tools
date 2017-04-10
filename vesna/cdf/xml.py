import datetime
import dateutil.parser
from lxml import etree
import json
import os.path
import time
import uuid

from vesna import cdf

_METADATA_HEADER = "Additional VESNA metadata follows:\n\n"

def _metadata_encode(obj, string=''):
	i = string.find(_METADATA_HEADER)
	if i != -1:
		string = string[:i]

	return string + _METADATA_HEADER + json.dumps(obj, indent=4)

def _metadata_decode(string):
	i = string.find(_METADATA_HEADER)
	if i != -1:
		return json.loads(string[i+len(_METADATA_HEADER):])

def text_or_none(xml_tree, xpath):
	t = xml_tree.find(xpath)
	if t is not None:
		return t.text
	else:
		return None

class CDFXMLExperiment:
	def __init__(self, experiment):
		self.exp = experiment

	def get_experiment(self):
		return self.exp

	@classmethod
	def load(cls, f):
		root = etree.parse(f)

		exp = cls._from_xml(root)

		return cls(exp)

	@classmethod
	def _from_xml(cls, root):
		title = text_or_none(root, "experimentAbstract/title")

		tag = text_or_none(root, "experimentAbstract/uniqueCREWTag")

		summary = text_or_none(root, "experimentAbstract/experimentSummary")

		release_date = text_or_none(root, "experimentAbstract/releaseDate")
		release_date = dateutil.parser.parse(release_date)

		methodology = []
		for method in root.findall("experimentAbstract/collectionMethodology"):
			methodology.append(method.text)

		related_experiments = text_or_none(root, "experimentAbstract/relatedExperiments")

		extra = None

		notes = []
		for note in root.findall("experimentAbstract/notes"):

			o = _metadata_decode(note.text)
			if o:
				extra = o
			else:
				notes.append(note.text)

		experiment = cdf.CDFExperiment(
				title=title,
				summary=summary,
				release_date=release_date,
				methodology=methodology,
				related_experiments=related_experiments,
				notes=notes)


		for author in root.findall("experimentAbstract/author"):
			experiment.add_author(cls._author_from_xml(author))

		for document in root.findall("experimentAbstract/furtherDocumentation"):
			experiment.add_document(cls._document_from_xml(document))


		start_hz = float(text_or_none(root, "metaInformation/radioFrequency/startFrequency"))
		stop_hz = float(text_or_none(root, "metaInformation/radioFrequency/stopFrequency"))
		step_hz = extra['step_hz']

		experiment.set_frequency_range(start_hz, stop_hz, step_hz)


		duration = extra['duration']
		experiment.set_duration(duration)


		devices = {}
		for d in root.findall("metaInformation/device"):
			device = cls._device_from_xml(d)
			devices[device.key()] = device

		interference = root.find("metaInformation/radioFrequency/interferenceSources")
		cls._interferers_from_xml(interference, experiment, devices)

		for device in devices.values():
			experiment.add_device(device)

		return experiment

	@classmethod
	def _author_from_xml(cls, root):
		
		name = text_or_none(root, "name")
		email = text_or_none(root, "email")

		address = []
		for t in root.findall("address"):
			address.append(t.text)

		phone = []
		for t in root.findall("phone"):
			phone.append(t.text)

		institution = []
		for t in root.findall("institution"):
			institution.append(t.text)

		return cdf.CDFAuthor(
				name=name,
				email=email,
				address=address,
				phone=phone,
				institution=institution)

	@classmethod
	def _document_from_xml(cls, root):
		
		description = []
		for t in root.findall("description"):
			description.append(t.text)

		bibtex = []
		for t in root.findall("bibtex"):
			bibtex.append(t.text)

		return cdf.CDFDocument(
				description=description,
				bibtex=bibtex)

	@classmethod
	def _device_from_xml(cls, root):
		extra = _metadata_decode(text_or_none(root, "description"))
		return cdf.CDFDevice(**extra)

	@classmethod
	def _interferers_from_xml(cls, root, experiment, devices):
		if not root.text:
			return

		extra_interferers = _metadata_decode(root.text)

		for extra_interferer in extra_interferers['interferers']:

			device_key = tuple(extra_interferer['device'])
			device = devices.pop(device_key)

			interferer = cdf.CDFInterferer(device=device)

			experiment.add_interferer(interferer)

			for program in extra_interferer['programs']:
				interferer.add_program(cdf.CDFInterfererProgram(**program))

	def _format_date(self, date):
		return date.isoformat()

	def _to_xml(self):
		root = etree.Element("experimentDescription")


		abstract = etree.SubElement(root, "experimentAbstract")

		title = etree.SubElement(abstract, "title")
		title.text = self.exp.title

		tag = etree.SubElement(abstract, "uniqueCREWTag")
		tag.text = self.exp.tag

		for author in self.exp.authors:
			abstract.append(self._author_to_xml(author))

		date = etree.SubElement(abstract, "releaseDate")
		date.text = self._format_date(self.exp.release_date)

		summary = etree.SubElement(abstract, "experimentSummary")
		summary.text = self.exp.summary

		for t in self.exp.methodology:
			method = etree.SubElement(abstract, "collectionMethodology")
			method.text = t

		for document in self.exp.documentation:
			abstract.append(self._document_to_xml(document))

		related = etree.SubElement(abstract, "relatedExperiments")
		related.text = self.exp.related_experiments

		ext_note = _metadata_encode({
			"duration": self.exp.duration,
			"step_hz": self.exp.step_hz})

		for t in self.exp.notes + [ext_note]:
			note = etree.SubElement(abstract, "notes")
			note.text = t


		meta = etree.SubElement(root, "metaInformation")

		for device in self.exp.iter_all_devices():
			meta.append(self._device_to_xml(device))

		location = etree.SubElement(meta, "location")

		# FIXME
		layout = etree.SubElement(location, "layout")
		mobility = etree.SubElement(location, "mobility")

		# FIXME
		date = etree.SubElement(meta, "date")
		date.text = self._format_date(datetime.datetime.now())

		rf = etree.SubElement(meta, "radioFrequency")

		start = etree.SubElement(rf, "startFrequency")
		start.text = str(self.exp.start_hz)

		stop = etree.SubElement(rf, "stopFrequency")
		stop.text = str(self.exp.stop_hz)

		rf.append(self._interferers_to_xml())

		trace = etree.XML("""<traceDescription><format>Tab-separated-values file with timestamp, frequency, power triplets.</format><fileFormat><header>Comment line, starting with #</header><collectedMetrics><name>time</name><unitOfMeasurements>s</unitOfMeasurements></collectedMetrics><collectedMetrics><name>frequency</name><unitOfMeasurements>Hz</unitOfMeasurements></collectedMetrics><collectedMetrics><name>power</name><unitOfMeasurements>dBm</unitOfMeasurements></collectedMetrics></fileFormat></traceDescription>""")

		meta.append(trace)


		for iteration in self.exp.iterations:
			if iteration.start_time:
				root.append(self._iteration_to_xml(iteration))

		tree = etree.ElementTree(root)
		return tree

	def _author_to_xml(self, author):
		root = etree.Element("author")

		name = etree.SubElement(root, "name")
		name.text = author.name

		email = etree.SubElement(root, "email")
		email.text = author.email

		for t in author.address:
			address = etree.SubElement(root, "address")
			address.text = t

		for t in author.phone:
			phone = etree.SubElement(root, "phone")
			phone.text = t

		for t in author.institution:
			institution = etree.SubElement(root, "institution")
			institution.text = t

		return root

	def _document_to_xml(self, document):
		root = etree.Element("furtherDocumentation")

		for t in document.description:
			description = etree.SubElement(root, "description")
			description.text = t

		for t in document.bibtex:
			bibtex = etree.SubElement(root, "bibtex")
			bibtex.text = t

		return root

	def _device_to_xml(self, device):
		root = etree.Element("device")

		name = etree.SubElement(root, "name")
		name.text = "VESNA node %d" % device.addr

		description = etree.SubElement(root, "description")
		description.text = _metadata_encode({
			"base_url": device.base_url,
			"cluster_id": device.cluster_id,
			"addr": device.addr})

		return root

	def _iteration_to_xml(self, iteration):
		root = etree.Element("experimentIteration")

		time = etree.SubElement(root, "time")

		start = etree.SubElement(time, "starttime")
		start.text = self._format_date(iteration.start_time)

		end = etree.SubElement(time, "endtime")
		end.text = self._format_date(iteration.end_time)

		for tracefile in iteration.tracefiles:
			path = etree.SubElement(root, "traceFile")
			path.text = tracefile

		return root

	def _interferers_to_xml(self):

		i_list = []
		for interferer in self.exp.interferers:
			p_list = []
			for program in interferer.programs:
				p_struct = {
					'center_hz': program.center_hz,
					'power_dbm': program.power_dbm,
					'start_time': program.start_time,
					'end_time': program.end_time }
				p_list.append(p_struct)

			i_struct = {
				'device': interferer.device.key(),
				'programs': p_list }

			i_list.append(i_struct)

		interference = etree.Element("interferenceSources")
		interference.text = _metadata_encode({"interferers": i_list})

		return interference

	def save(self, f):
		tree = self._to_xml()
		tree.write(f, pretty_print=True, encoding='utf8')

	def save_all(self, path=None):
		if path is None:
			path = self.exp.tag

		cdf_path = path + ".cdf"
		dat_path = path + ".dat"

		try:
			os.mkdir(dat_path)
		except OSError:
			pass

		for iteration in self.exp.iterations:
			for i, sensor in enumerate(iteration.sensors):

				n = "data_%s_node_%d_%d.dat" % (
						iteration.start_time.strftime("%Y%m%d"),
						sensor.sensor.alh.addr,
						i)
				p = os.path.join(dat_path, n)

				sensor.result.write(p)

				iteration.tracefiles.append(p)

		self.save(open(cdf_path, "w"))
