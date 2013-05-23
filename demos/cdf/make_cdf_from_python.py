import datetime
import logging
from vesna import cdf
from vesna.cdf.xml import CDFXMLExperiment

logging.basicConfig(level=logging.INFO)

def main():
	now = datetime.datetime.now()

	e = cdf.CDFExperiment(
			title="Test experiment",
			summary="Experiment summary",
			release_date=now,
			methodology="Collection methodology",
			related_experiments="Related experiments",
			notes="Notes")

	a = cdf.CDFAuthor(
			name="John",
			email="john@example.com",
			address="Nowhere",
			phone="555 555 555",
			institution="Institute of Imaginary Science")
	e.add_author(a)

	d = cdf.CDFDocument(
			description="A document",
			bibtex="BibTeX")
	e.add_document(d)

	e.set_frequency_range(
			start_hz=2400e6,
			stop_hz=2450e6,
			step_hz=400e3)

	d = cdf.CDFDevice(
			base_url="https://crn.log-a-tec.eu/communicator", 
			cluster_id=9501,
			addr=40)

	e.add_device(d)

	d = cdf.CDFDevice(
			base_url="https://crn.log-a-tec.eu/communicator", 
			cluster_id=9501,
			addr=34)

	i = cdf.CDFInterferer(
			device=d)

	p = cdf.CDFInterfererProgram(
			center_hz=2420e6,
			power_dbm=0,
			start_time=0,
			end_time=15)

	i.add_program(p)

	e.add_interferer(i)

	e.set_duration(15)

	i = cdf.CDFExperimentIteration()

	e.run(i)

	ex = CDFXMLExperiment(e)

	ex.save_all("make_cdf_from_python")

main()
