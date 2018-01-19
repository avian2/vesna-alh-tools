from vesna import alh
from vesna.alh.uwbnode import UWBNode, RadioSettings
import serial

if __name__ == "__main__":
	f =  serial.Serial("/dev/ttyUSB0", 921600, timeout=1)
	node = alh.ALHTerminal(f)

	# UWB node object
	uwbnode = UWBNode(node)

	# get current radio settings from node
	settings = RadioSettings()
	settings = uwbnode.get_radio_settings()
	# print current settings in dictionary form
	print(settings.get_dict())

	# set desired radio settings
	settings.channel = 5
	settings.channel_code = 9
	settings.prf = 64
	settings.datarate = 110
	settings.preamble_length = 1024
	settings.pac_size = 32
	settings.nssfd = 1
	settings.sfd_timeout = 1024 + 32 + 1

	# send settings to UWB radio
	uwbnode.setup_radio(settings)

	for i in range(100):
		if(uwbnode.check_pending_measurement()):
			res = uwbnode.get_last_range_data()
			print("Range: %s m" % res['range'])
			print("NodeID: %s" % uwbnode.get_sensor_id())
			print("DestID: %s" % res['dest_id'])
			print("RSS: %5.2f dBm" % res['rss'])
			print("RSS_FP: %5.2f dBm" % res['rss_fp'])
			print("Noise_STDEV: %s" % res['noise_stdev'])
			print("Max_noise: %s" % res['max_noise'])
			print("RXPACC: %s" % res['rxpacc'])
			print("FP_index: %s" % res['fp_index'])
			#print(res['cir'])
			print()

