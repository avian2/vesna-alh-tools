import binascii
import re
import serial
import struct
import time

class ALHProtocolException(Exception):
	def __init__(self, msg):
		if msg.endswith(self.TERMINATOR):
			msg = msg[:-len(self.TERMINATOR)].strip()
		super(Exception, self).__init__(msg)

class JunkInput(ALHProtocolException):
	TERMINATOR = "JUNK-INPUT\r\n"

class CorruptedData(ALHProtocolException): 
	TERMINATOR = "CORRUPTED-DATA\r\n"

class ALHRandomError(Exception): pass

"""Almost-like-HTTP protocol handler
"""
class ALHProtocol:
	RESPONSE_TERMINATOR = "\r\nOK\r\n"

	def __init__(self, f):
		self.f = f

	def _send(self, data):
		self.f.write(data)

		resp = ""
		while not resp.endswith(self.RESPONSE_TERMINATOR):
			resp += self.f.read()

		return resp[:-len(self.RESPONSE_TERMINATOR)]

	def _recover(self):
		self._send("\r\n" * 5)

	def _crc(self, data):
		return binascii.crc32(data)

	def _send_with_error(self, data):
		resp = self._send(data)
		if resp.endswith("JUNK-INPUT\r\n"):
			self._recover()
			raise JunkInput(resp)
		if resp.endswith("CORRUPTED-DATA\r\n"):
			raise CorruptedData(resp)

		# this usually, but not always, means something went
		# wrong.
		if "error" in resp.lower() or "warning" in resp.lower():
			raise ALHRandomError(resp)
		
		return resp

	def get(self, resource, *args):
		arg = "".join(args)
		return self._send_with_error("get %s?%s\r\n" % (resource, arg))

	def post(self, resource, data, *args):
		arg = "".join(args)

		req = "post %s?%s\r\nlength=%d\r\n%s\r\n" % (
				resource, arg, len(data), data)

		crc = self._crc(req)

		req += "crc=%d\r\n" % crc

		return self._send_with_error(req)

class ALHProtocolRemote(ALHProtocol):
	def _recover_remote(self, addr):
		self.post("radio/noderesetparser", "", "%d" % addr)

	def _check_for_junk_state(self, addr, message):
		g = re.search("NODES:Node ([0-9]+) parser is in junk state\r\nERROR", message)
		if g:
			assert(int(g.group(1)) == addr)
			self._recover_remote(addr)

	def get_remote(self, addr, resource, *args):
		try:
			return self.get("nodes", "%d/%s?" % (addr, resource), *args)
		except ALHRandomError, e:
			self._check_for_junk_state(addr, str(e))
			raise

	def post_remote(self, addr, resource, data, *args):
		try:
			return self.post("nodes", data, "%d/%s?" % (addr, resource), *args)
		except ALHRandomError, e:
			self._check_for_junk_state(addr, str(e))
			raise

def main():
	f = serial.Serial("/dev/ttyUSB0", 115200, timeout=10)
	vesna = ALHProtocolRemote(f)

#	node8req = ""
#	node7req = ""
#
#	for n in xrange(8):
#		node8req += "in %d sec for 1 sec with dev 0 conf 0 channel %d power 0\r\n" % (5 + 0 + n, n*30)
#		node7req += "in %d sec for 1 sec with dev 0 conf 0 channel %d power 0\r\n" % (5 + 7 - n, n*30)
#
#	vesna.post_remote(8, "generator/program", node8req)
#	vesna.post_remote(7, "generator/program", node7req)

	print vesna.get_remote(7, "sensing/deviceConfigList")
	print vesna.get_remote(8, "generator/deviceConfigList")

	vesna.post_remote(8, "generator/program", 
			"in 5 sec for 10 sec with dev 0 conf 0 channel 20 power 0")

	vesna.post_remote(7, "sensing/freeUpDataSlot", "1", "id=1")
	vesna.post_remote(7, "sensing/program",
			"in 5 sec for 20 sec with dev 0 conf 1 ch 0:1:20 to slot 1")
	

	resp = ""
	while "status=COMPLETE" not in resp:
		time.sleep(1)
		resp = vesna.get_remote(7, "sensing/slotInformation", "id=1")

	g = re.search("size=([0-9]+)", resp)
	resp = ""
	size = int(g.group(1))
	p = 0
	while p < size:
		chunk = min(512, size - p)

		data = vesna.get_remote(7, "sensing/slotDataBinary", 
				"id=1&start=%d&size=%d" % (p, chunk))
	
		d = data[:-4]
		crc = struct.unpack("i", data[-4:])[0]
		crc2 = binascii.crc32(d)
		print crc, crc2
		if crc != crc2:
			print "ERROR"

		resp += d

		p += 512

	f = open("raw", "w")
	f.write(resp)

	f = open("out", "w")
	ch = 0
	t = 0
	for n in xrange(0, len(resp), 2):
		dbm = struct.unpack("h", resp[n:n+2])[0]*1e-2

		f.write("%f\t%f\t%f\n" % (ch, t, dbm))

		ch += 1
		if(ch == 20):
			ch = 0
			t += 1
			f.write("\n")

main()
