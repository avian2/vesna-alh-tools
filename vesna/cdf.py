import datetime
from lxml import etree
import json
import uuid
from vesna import alh

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

class CDFDevice:
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
	def __init__(self, start_time, end_time, slot_id):
		self.start_time = start_time
		self.end_time = end_time
		self.slot_id = slot_id

class CDFExperimentSensor: pass

class CDFExperiment:
	def __init__(self, title, summary, start_hz, stop_hz, step_hz, tag=None, _xml_tree=None):
		self.devices = []
		self.title = title
		self.summary = summary
		self.start_hz = start_hz
		self.stop_hz = stop_hz
		self.step_hz = step_hz

		if tag is None:
			tag = "vesna-alh-tools-" + str(uuid.uuid4())

		self.tag = tag

		self._unsaved_iterations = []

		if not _xml_tree:
			self.xml_tree = etree.ElementTree(etree.XML("""<experimentDescription>
	<experimentAbstract>
	</experimentAbstract>
	<metaInformation>
		<radioFrequency>
			<startFrequency>%(start_hz)d</startFrequency>
			<stopFrequency>%(stop_hz)d</stopFrequency>
		</radioFrequency>
	</metaInformation>
	<experimentIteration>
	</experimentIteration>
</experimentDescription>""" % {	"start_hz": start_hz, "stop_hz": stop_hz } ))

			abstract = self.xml_tree.find("experimentAbstract")

			title_ = etree.SubElement(abstract, "title")
			title_.text = title

			tag_ = etree.SubElement(abstract, "uniqueCREWTag")
			tag_.text = tag

			date_ = etree.SubElement(abstract, "releaseDate")
			date_.text = str(datetime.datetime.now())

			summary_ = etree.SubElement(abstract, "experimentSummary")
			summary_.text = summary

			etree.SubElement(abstract, "relatedExperiments")

			notes_ = etree.SubElement(abstract, "notes")
			notes_.text = _metadata_encode({"step_hz": step_hz})

	def add_device(self, device, _add_to_tree=True):
		self.devices.append(device)

		if _add_to_tree:
			self.xml_tree.find("metaInformation").append(device._to_xml())

	@classmethod
	def load(cls, f):
		xml_tree = etree.parse(f)

		start_hz = int(xml_tree.find("metaInformation/radioFrequency/startFrequency").text)
		stop_hz = int(xml_tree.find("metaInformation/radioFrequency/stopFrequency").text)

		title = xml_tree.find("experimentAbstract/title").text
		summary = xml_tree.find("experimentAbstract/experimentSummary").text
		tag = xml_tree.find("experimentAbstract/uniqueCREWTag").text

		obj = _metadata_decode(xml_tree.find("experimentAbstract/notes").text)
		step_hz = obj['step_hz']

		e = cls(title, summary, start_hz, stop_hz, step_hz, tag=tag, _xml_tree=xml_tree)

		for device in xml_tree.findall("metaInformation/device"):
			e.add_device(CDFDevice._from_xml(device), _add_to_tree=False)

		return e

	def save(self, f):
		self.xml_tree.write(f, pretty_print=True)

	def add_credentials(self, base_url):
		return base_url

	def log(self, msg):
		alh.common.log(msg)

	def _get_coordinators(self):
		coordinators = {}

		for device in self.devices:
			args = (device.base_url, device.cluster_id)
			if args not in coordinators:
				coordinator = alh.ALHWeb(*args)
				coordinator = self.log

				coordinator.post("prog/firstCall", "1")

				coordinators[args] = coordinator

		return coordinators

	def _get_nodes(self):
		coordinators = self._get_coordinators(self)

		nodes = []

		for device in self.devices:
			coordinator = coordinators[device.base_url, device.cluster_id]
			node = alh.ALHProxy(coordinator, device.addr)

			node.post("prog/firstCall", "1")

			nodes.append(node)

		return nodes

	def run(self, iteration):
		sensors = iteration.sensors = []

		for node in self._get_nodes():
			sensor = CDFExperimentSensor()

			sensor.sensor = alh.spectrumsensor.SpectrumSensor(node)

			config_list = sensor.sensor.get_config_list()

			sweep_config = config_list.get_sweep_config(
				start_hz=self.start_hz,
				stop_hz=self.stop_hz,
				step_hz=self.step_hz)

			assert sweep_config is not None

			sensor.program = SpectrumSensorProgram(
					sweep_config, 
					iteration.start_time,
					iteration.end_time - iteration.start_time,
					slot_id=iteration.slot_id)

			sensors.append(sensor)

		for sensor in sensors:
			sensor.sensor.program(sensor.program)

		for sensor in sensors:
			while not sensor.sensor.is_complete(sensor.program):
				self.log("*** waiting...")
				time.sleep(2)

				if time.time() > (iteration.end_time + 30):
					raise Exception("Something went wrong")

			self.log("*** experiment is finished. retrieving data.")

			sensor.result = sensor.sensor.retrieve(program)

			#try:
			#	os.mkdir("data")
			#except OSError:
			#	pass
			#
			#result.write("data/node_%d.dat" % (sensor.alh.addr,))

		self._unsaved_iterations.append(iteration)

#ex = CDFExperiment.load("cdf/VESNA_SS_24GHz.xml")
