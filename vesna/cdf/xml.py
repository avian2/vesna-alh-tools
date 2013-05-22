import datetime
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
	if t:
		return t.text
	else:
		return None

class CDFXMLDevice(cdf.CDFDevice):
	def __init__(self, base_url, cluster_id, addr):
		self.base_url = base_url
		self.cluster_id = cluster_id
		self.addr = addr

	@classmethod
	def _from_xml(cls, tree):
		obj = _metadata_decode(tree.find("description").text)
		return cls(obj['base_url'], obj['cluster_id'], obj['addr'])

	def _to_xml(self):
		tree = etree.Element("device")

		name = etree.SubElement(tree, "name")
		name.text = "VESNA node %d" % (self.addr,)

		description = etree.SubElement(tree, "description")
		description.text = _metadata_encode({
			"base_url": self.base_url,
			"cluster_id": self.cluster_id,
			"addr": self.addr})

		return tree

class CDFExperimentIteration:
	def __init__(self, start_time, end_time, slot_id=10):
		self.start_time = start_time
		self.end_time = end_time
		self.slot_id = slot_id

class CDFXMLExperiment:
	def __init__(self, experiment):
		self.exp = experiment

	def get_experiment():
		return self.exp

	@classmethod
	def load(cls, f):
		xml_tree = etree.parse(f)


		title = text_or_none(xml_tree, "experimentAbstract/title")

		tag = text_or_none(xml_tree, "experimentAbstract/uniqueCREWTag")

		authors = []
		for author in xml_tree.findall("experimentAbstract/author"):
			authors.append(CDFXMLAuthor.from_tree(author))

		release_date_t = text_or_none(xml_tree, "experimentAbstract/releaseDate")
		release_date = datetime.datetime.strptime(release_date_t, "%Y-%m-%d")

		summary = text_or_none(xml_tree, "experimentAbstract/experimentSummary")

		methodology = []
		for m in xml_tree.findall("experimentAbstract/collectionMethodology"):
			methodology.append(m.text)

		documentation = []
		for document in xml_tree.findall("experimentAbstract/furtherDocumentation"):
			documentation.append(CDFXMLDocument.from_tree(document))

		related_experiments = text_or_none(xml_tree, "experimentAbstract/relatedExperiments")

		extra = None

		notes = []
		for note in xml_tree.findall("experimentAbstract/notes"):
			notes.append(note.text)

			o = _metadata_decode(note.text)
			if o:
				extra = o

		experiment = cls(
				title=title, 
				tag=tag,
				authors=authors,
				release_date=release_date,
				summary=summary,
				methodology=methodology,
				documentation=documentation,
				related_experiments=related_experiments,
				notes=notes)


		start_hz = int(text_or_none(xml_tree, "metaInformation/radioFrequency/startFrequency"))
		stop_hz = int(text_or_none(xml_tree, "metaInformation/radioFrequency/stopFrequency"))
		step_hz = extra['step_hz']

		experiment.set_frequency_range(start_hz, stop_hz, step_hz)


		duration = datetime.timedelta(seconds=extra['duration'])
		experiment.set_duration(duration)


		devices = {}
		for d in xml_tree.findall("metaInformation/device"):
			device = CDFXMLDevice.from_tree(d)
			devices[device.key()] = device


		extra_interferers = _metadata_decode(xml_tree.find("metaInformation/radioFrequency/interferenceSources"))
		for extra_interferer in extra_interferers:
			device = devices.pop(extra_interferer.device)

			start_time = datetime.timedelta(seconds=extra_interferer['start_time'])
			end_time = datetime.timedelta(seconds=extra_interferer['end_time'])

			interferer = CDFInterferer(
					device=device,
					center_hz=extra_interferer['center_hz'],
					power_dbm=extra_interferer['power_dbm'],
					device_id=extra_interferer['device_id'],
					config_id=extra_interferer['config_id'],
					start_time=start_time,
					end_time=end_time)

			experiment.add_interferer(interferer)

		for device in devices.itervalues():
			experiment.add_device(device)

		return experiment

	def _format_date(self, date):
		return str(date)

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

		ext_note = _metadata_encode({"duration": self.exp.duration})

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


		i_list = []
		for interferer in self.exp.interferers:
			i_struct = {
				'device': interferer.device.key(),
				'center_hz': interferer.center_hz,
				'power_dbm': interferer.power_dbm,
				'start_time': interferer.start_time,
				'end_time': interferer.end_time }
			i_list.append(i_struct)

		interference = etree.SubElement(rf, "interferenceSources")
		interference.text = _metadata_encode({"interferers": i_list})

		trace = etree.SubElement(meta, "traceDescription")

		trace = etree.XML("""<traceDescription><format>Tab-separated-values file with timestamp, frequency, power triplets.</format><fileFormat><header>Comment line, starting with #</header><collectedMetrics><name>time</name><unitOfMeasurements>s</unitOfMeasurements></collectedMetrics><collectedMetrics><name>frequency</name><unitOfMeasurements>Hz</unitOfMeasurements></collectedMetrics><collectedMetrics><name>power</name><unitOfMeasurements>dBm</unitOfMeasurements></collectedMetrics></fileFormat></traceDescription>""")

		meta.append(trace)

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

	def save(self, f):
		tree = self._to_xml()
		tree.write(f, pretty_print=True, encoding='utf8')

	def save_all(self, path=None):
		if path is None:
			path = self.tag

		cdf_path = path + ".cdf"
		dat_path = path + ".dat"

		try:
			os.mkdir(dat_path)
		except OSError:
			pass

		for iteration in self._unsaved_iterations:
			iteration_ = etree.SubElement(self.xml_tree.getroot(), "experimentIteration")

			time_ = etree.SubElement(iteration_, "time")

			starttime_ = etree.SubElement(time_, "starttime")
			starttime_.text = datetime.datetime.fromtimestamp(iteration.start_time).isoformat()

			endtime_ = etree.SubElement(time_, "endtime")
			endtime_.text = datetime.datetime.fromtimestamp(iteration.end_time).isoformat()

			for i, sensor in enumerate(iteration.sensors):

				n = "data_%d_node_%d_%d.dat" % (
						iteration.start_time,
						sensor.sensor.alh.addr,
						i)
				p = os.path.join(dat_path, n)

				sensor.result.write(p)

				tracefile_ = etree.SubElement(iteration_, "traceFile")
				tracefile_.text = p

		self.save(open(cdf_path, "w"))

		self._unsaved_iterations = []
