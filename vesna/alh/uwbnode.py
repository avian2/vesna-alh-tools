import math
import numpy as np


def parseCIR2Complex(data):
	"""make a list of strings with complex cir points
	['2+3j','3+2j']
	"""
	length = int(len(data) / 4)
	tempreal = None
	tempcpx = None
	cpx_data = []
	for x in range(length):
		tempreal = ((ord(data[(x * 4)])) << 8) + (ord(data[(x * 4) + 1]))
		# convert unsigned integer to signed integer
		if (tempreal & 0x8000):
			tempreal = -0x10000 + tempreal
		tempcpx = ((ord(data[(x * 4) + 2])) << 8) + (ord(data[(x * 4) + 3]))
		if (tempcpx & 0x8000):
			tempcpx = -0x10000 + tempcpx
		cpx_data.append(str(complex(tempreal, tempcpx)))

	return cpx_data

def signal_power(datadict, fp1, fp2, fp3, cir_power, prfr):
	"""
		calculate vector of first path power and total signal power
	"""
	# RCPE first path
	rcpe_fp = 10 * np.log10((np.power(fp1, 2) + np.power(fp2, 2) + np.power(fp3, 2)) / (np.power(datadict['rxpacc'], 2)))
	# RCPE
	if cir_power == 0.0:
		rcpe = rcpe_fp
	else:
		rcpe = 10 * np.log10((cir_power * math.pow(2, 17)) / (np.power(datadict['rxpacc'], 2)))

	# compensate for PRFR
	if int(prfr) == 16:
		rcpe = rcpe - 115.72
		rcpe_fp = rcpe_fp - 115.72
	else:
		rcpe = rcpe - 121.74
		rcpe_fp = rcpe_fp - 121.74

	return rcpe, rcpe_fp


def dataLineToDictionary(line):
	"""
	This function translates uwb device response to results dictionary
	:param line: response text line from uwb device
	:return: dictionary with measurement results
	"""
	msg_dict = {'node_id': None, 'dest_id': None, 'range': None, 'rss': None,
				'rss_fp': None, 'noise_stdev': None, 'max_noise': None,
				'rxpacc': None, 'fp_index': None, 'cir': None}

	# Node ID
	idx = line.find("SRC:")
	if idx >= 0:
		temp_data = line[( idx +4):( idx + 4 +16)]
		msg_dict['node_id'] = temp_data
	# Destination_ID
	idx = line.find("DEST:")
	if idx >= 0:
		temp_data = line[( idx +5):( idx + 16 +5)]
		msg_dict['dest_id'] = temp_data
	# Range
	idx = line.find("DIST:")
	if idx >= 0:
		temp_data = float(line[( idx +5):( idx + 5 +5)])
		msg_dict['range'] = temp_data
	# FP_index
	idx = line.find("FP_INDEX:")
	if idx >= 0:
		temp_data = int(line[( idx +9):( idx + 9 +3)])
		msg_dict['fp_index'] = temp_data
	# FP_point1
	idx = line.find("FP_AMPL1:")
	if idx >= 0:
		temp_data = int(line[( idx +9):( idx + 9 +5)])
		fp1 = temp_data
	# FP_point2
	idx = line.find("FP_AMPL2:")
	if idx >= 0:
		temp_data = int(line[( idx +9):( idx + 9 +5)])
		fp2 = temp_data
	# FP_point3
	idx = line.find("FP_AMPL3:")
	if idx >= 0:
		temp_data = int(line[( idx +9):( idx + 9 +5)])
		fp3 = temp_data
	# Noise_STDEV
	idx = line.find("STD_NOISE:")
	if idx >= 0:
		temp_data = int(line[( idx +10):( idx + 10 +5)])
		msg_dict['noise_stdev'] = temp_data
	# CIR_power
	idx = line.find("CIR_PWR:")
	if idx >= 0:
		temp_data = int(line[( idx +8):( idx + 8 +5)])
		cir_power = temp_data
	# Max_noise
	idx = line.find("MAX_NOISE:")
	if idx >= 0:
		temp_data = int(line[( idx +10):( idx + 10 +5)])
		msg_dict['max_noise'] = temp_data
	# RXPACC
	idx = line.find("RXPACC:")
	if idx >= 0:
		temp_data = int(line[( idx +7):( idx + 7 +5)])
		msg_dict['rxpacc'] = temp_data
	# PRFR
	idx = line.find("PRFR:")
	if idx >= 0:
		temp_data = int(line[( idx +5):( idx + 5 +2)])
		prfr = temp_data
	# RSS and RSS_FP values
	msg_dict['rss'], msg_dict['rss_fp'] = signal_power(msg_dict, fp1, fp2, fp3, cir_power, prfr)

	return msg_dict


class RadioSettings:
	"""
	This class represents object with available radio settings
	:param channel: selected channel (options: 1,2,3,4,5,7)
	:param channel_code: channel-specific code (please look at DW1000 user manual)
	:param prf: pulse repetition frequency (16MHz:16 or 64MHz:64)
	:param datarate: bitrate (110k:110, 850k: 850 or 6.8M:6800)
	:param preamble_length: preamble length in symbols (64, 128, 256, 512, 1024, 1536, 2048 or 4096)
	:param pac_size: preamble acquisition chunk size (8, 16, 32 or 64)
	:param nssfd: non-standar sfd (0 or 1)
	:param sfd_timeout: frame delimiter timeout or time in symbols before start-of-frame delimiter timeout occurs (normally preamble_length + pac_size + 1)
	"""
	def __init__(self, channel=4, channel_code=17, prf=64, datarate=110, preamble_length=1024, pac_size=32, nssfd=1, sfd_timeout=1057):
		self.channel = channel
		self.channel_code = channel_code
		self.prf = prf
		self.datarate = datarate
		self.preamble_length = preamble_length
		self.pac_size = pac_size
		self.nssfd = nssfd
		self.sfd_timeout = sfd_timeout

	def get_dict(self):
		""" return settings in dictionary form """
		settings_dict = {'ch': self.channel, 'ch_code': self.channel_code, 'prf': self.prf, 'dr': self.datarate,
							  'plen': self.preamble_length, 'pac': self.pac_size, 'nssfd': self.nssfd,
							  'sfdto': self.sfd_timeout}

		return settings_dict


class UWBNode:
	"""
	ALH node abstracting an UWB node functionality

	:param alh: ALH implementation used to communicate with the node
	"""
	def __init__(self, alh):
		self.alh = alh

	def get_sensor_id(self):
		""" read the ID of UWB node """
		response = self.alh.get("node_id")

		return response.text[:-1]

	def get_radio_settings(self):
		""" read current uwb radio settings """
		settings = RadioSettings()
		response = self.alh.get("radio/settings")
		response = response.text.split('&')
		settings.channel = int(response[0].split('=')[1])
		settings.channel_code = int(response[1].split('=')[1])
		settings.prf = int(response[2].split('=')[1])
		settings.datarate = int(response[3].split('=')[1])
		settings.preamble_length = int(response[4].split('=')[1])
		settings.pac_size = int(response[5].split('=')[1])
		settings.nssfd = int(response[6].split('=')[1])
		settings.sfd_timeout = int(response[7].split('=')[1])

		return settings

	def setup_radio(self, settings):
		""" setup radio from RadioSettings object """

		self.alh.post("radio/settings", "ch=%1u&ch_code=%2u&prf=%2u&dr=%4u&plen=%4u&pac=%2u&nssfd=%1u&sfdto=%4u" %
							(settings.channel, settings.channel_code, settings.prf, settings.datarate,
							settings.preamble_length, settings.pac_size, settings.nssfd, settings.sfd_timeout))

	def get_last_range_data(self):
		""" return measurements data """
		response = self.alh.get("measurement")
		data = dataLineToDictionary(response.text)
		idx = response.text.find("DATALEN{")
		if idx >= 0:
			#datalen = int(response[idx+8:idx+12])
			data['cir'] = parseCIR2Complex(response.text[idx+14:-1])

		return data

	def check_pending_measurement(self):
		""" check if measurement data is ready for transfer """
		response = self.alh.get("pending")

		return int(response.text)
