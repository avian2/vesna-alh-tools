from alh import alh
from alh.spectrum import *
from alh.common import log
import serial
import string
import sys
import time

def ism_24ghz(time_start, nodef):
	SignalGenerationRun(
			nodef(2),
			time_start = time_start + 5.0,
			time_duration = 10,
			device = 0,
			config = 0,
			channel = 50,
			power = 0).program()

	SignalGenerationRun(
			nodef(17),
			time_start = time_start + 5.0,
			time_duration = 10,
			device = 0,
			config = 0,
			channel = 150,
			power = 0).program()
	
	return MultiNodeSpectrumSensingRun(
			[nodef(25), nodef(6)],
			time_start = time_start,
			time_duration = 20,
			device = 0,
			config = 0,
			ch_start = 0,
			ch_step = 1,
			ch_stop = 255,
			slot_id = 5)
	
def uhf_multiplex(time_start, nodef):
	return MultiNodeSpectrumSensingRun(
			[nodef(19)],
			time_start = time_start,
			time_duration = 60,
			device = 0,
			config = 0,
			ch_start = 0,
			ch_step = 1500,
			ch_stop = 392000,
			slot_id = 5)

def uhf_wireless_mic(time_start, nodef):
	SignalGenerationRun(
			nodef(8),
			time_start = time_start,
			time_duration = 50,
			device = 0,
			config = 0,
			channel = 0,
			power = 0).program()

	SignalGenerationRun(
			nodef(8),
			time_start = time_start + 60.0,
			time_duration = 50,
			device = 0,
			config = 0,
			channel = 10,
			power = 0).program()

	SignalGenerationRun(
			nodef(8),
			time_start = time_start + 120.0,
			time_duration = 50,
			device = 0,
			config = 0,
			channel = 20,
			power = 0).program()

	SignalGenerationRun(
			nodef(8),
			time_start = time_start + 180.0,
			time_duration = 50,
			device = 0,
			config = 0,
			channel = 30,
			power = 0).program()

	return MultiNodeSpectrumSensingRun(
			[nodef(20), nodef(19)],
			time_start = time_start,
			time_duration = 240,
			device = 0,
			config = 0,
			ch_start = 290000,
			ch_step = 500,
			ch_stop = 350000,
			slot_id = 5)

def main():
	#f = serial.Serial("/dev/ttyUSB0", 115200, timeout=10)
	#coor = alh.ALHTerminal(f)

	coor = alh.ALHWeb("https://crn.log-a-tec.eu/communicator", 10001)
	coor._log = log

	def nodef(addr):
		return alh.ALHProxy(coor, addr)
	
	time_start = time.time() + 10

	#experiment = ism_24ghz(time_start, nodef)
	#experiment = uhf_multiplex(time_start, nodef)
	experiment = uhf_wireless_mic(time_start, nodef)

	experiment.program()

	while not experiment.is_complete():
		print "waiting..."
		time.sleep(2)

	print "experiment is finished. retrieving data."

	results = experiment.retrieve()

	write_results("h", results, experiment)

main()
