import datetime
import json
import os.path
import time
import uuid
import vesna.alh
import vesna.alh.spectrumsensor
import vesna.alh.common

def force_list(v):
	if v is None:
		return []
	elif isinstance(v, str) or isinstance(v, unicode):
		return [ v ]
	else:
		v

class CDFError(Exception): pass

class CDFInterferer:
	def __init__(self, device, center_hz, power_dbm, start_time, end_time, 
			device_id=None, config_id=None):
		self.device = device
		self.center_hz = center_hz
		self.power_dbm = power_dbm
		self.device_id = device_id
		self.config_id = config_id
		self.start_time = start_time
		self.end_time = end_time

class CDFDevice:
	def __init__(self, base_url, cluster_id, addr):
		self.base_url = base_url
		self.cluster_id = cluster_id
		self.addr = addr

	def key(self):
		return (self.base_url, self.cluster_id, self.addr)

	def __str__(self):
		return "<CDFDevice base_url=%s cluster_id=%d addr=%d>" % (
				self.base_url, self.cluster_id, self.addr)

class CDFAuthor:
	def __init__(self, name, email, address=None, phone=None, institution=None):
		self.name = name
		self.email = email
		self.address = force_list(address)
		self.phone = force_list(phone)
		self.institution = force_list(institution)

class CDFDocument:
	def __init__(self, description=None, bibtex=None):
		self.description = force_list(description)
		self.bibtex = force_list(bibtex)

class CDFExperimentIteration:
	def __init__(self, start_time, end_time, slot_id=10):
		self.start_time = start_time
		self.end_time = end_time
		self.slot_id = slot_id

class CDFExperimentSensor: pass

class CDFExperimentInterferer: pass

class CDFExperiment:
	def __init__(self, title, summary, methodology=None, related_experiments, notes, 
			tag=None, release_date=None, authors=None, documentation=None, devices=None, 
			interferers=None):

		self.title = title

		if tag is not None:
			self.tag = tag
		else:
			self.tag = "vesna-alh-tools-" + str(uuid.uuid4())

		self.authors = force_list(authors)

		self.release_date = release_date

		self.summary = summary

		self.methodology = force_list(methodology)

		self.documentation = force_list(documentation)

		self.related_experiments = related_experiments

		self.notes = force_list(notes)

		self.start_hz = None
		self.stop_hz = None
		self.step_hz = None

		self.duration = None

		self.devices = force_list(devices)
		self.interferers = force_list(interferers)

		self.iterations = []

	def set_frequency_range(self, start_hz, stop_hz, step_hz):
		self.start_hz = start_hz
		self.stop_hz = stop_hz
		self.step_hz = step_hz

	def set_duration(self, duration):
		self.duration = duration

	def add_author(self, author):
		self.authors.append(author)

	def add_document(self, document):
		self.documentation.append(document)

	def add_device(self, device):
		self.devices.append(device)

	def add_interferer(self, interferer):
		self.interferers.append(interferer)

	def iter_all_devices(self):
		for device in self.devices:
			yield device

		for interferer in self.interferers:
			yield interferer.device

	def _get_coordinators(self):
		coordinators = {}

		for device in self.iter_all_devices():
			args = (device.base_url, device.cluster_id)
			if args not in coordinators:
				coordinator = vesna.alh.ALHWeb(*args)
				coordinator._log = self.log

				coordinator.post("prog/firstCall", "1")

				coordinators[args] = coordinator

		return coordinators

	def _get_nodes(self):
		coordinators = self._get_coordinators()

		nodes = {}

		for device in self.iter_all_devices():
			if device.key() not in nodes:
				coordinator = coordinators[device.base_url, device.cluster_id]

				node = vesna.alh.ALHProxy(coordinator, device.addr)

				node.post("prog/firstCall", "1")

				nodes[device.key()] = node
			else:
				raise CDFError("Device %s used more than once" % device)

		return nodes

	def run(self, iteration):
		sensors = iteration.sensors
		intererers = iteration.interferers

		nodes = self._get_nodes()

		for device in self.devices:
			sensor = CDFExperimentSensor()

			node = nodes[device.key()]
			sensor.sensor = vesna.alh.spectrumsensor.SpectrumSensor(node)

			config_list = sensor.sensor.get_config_list()

			sweep_config = config_list.get_sweep_config(
					start_hz=self.start_hz,
					stop_hz=self.stop_hz,
					step_hz=self.step_hz)

			if sweep_config is None:
				raise CDFError("Device %s cannot scan desired frequency range" % device)

			sensor.program = vesna.alh.spectrumsensor.SpectrumSensorProgram(
					sweep_config, 
					iteration.start_time,
					iteration.end_time - iteration.start_time,
					slot_id=iteration.slot_id)

			sensors.append(sensor)

		for interferer in self.interferers:
			einterferer = CDFExperimentInterferer()

			node = nodes[interferer.device.key()]
			einterferer.generator = vesna.alh.signalgenerator.SignalGenerator(node)

			config_list = einterferer.generator.get_config_list()

			tx_config = config_list.get_tx_config(
					f_hz=interferer.center_hz,
					power_dbm=interferer.power_dbm)

			if tx_config is None:
				raise CDFError("Device %s cannot transmit at desired "
						"frequency range" % device)

			einterferer.program = vesna.alh.signalgenerator.SignalGeneratorProgram(
					tx_config,
					interferer.start_time,
					interferer.end_time - interferer.start_time)

			interferers.append(einterferer)

		for sensor in sensors:
			sensor.sensor.program(sensor.program)
		for interferer in interferers:
			interferer.generator.program(einterferer.program)

		for sensor in sensors:
			while not sensor.sensor.is_complete(sensor.program):
				self.log("*** waiting...")
				time.sleep(2)

				if time.time() > (iteration.end_time + 30):
					raise Exception("Something went wrong")

			self.log("*** experiment is finished. retrieving data.")

			sensor.result = sensor.sensor.retrieve(sensor.program)

		self.iterations.append(iteration)
