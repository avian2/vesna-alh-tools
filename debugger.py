import binascii
import serial

class ALHProtocolException(Exception):
	def __init__(self, msg):
		if msg.endswith(self.TERMINATOR):
			msg = msg[:-len(self.TERMINATOR)].strip()
		super(Exception, self).__init__(msg)

class JunkInput(ALHProtocolException):
	TERMINATOR = "JUNK-INPUT\r\n"

class CorruptedData(ALHProtocolException): 
	TERMINATOR = "CORRUPTED-DATA\r\n"

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
	def get_remote(self, addr, resource, *args):
		return self.get("nodes", "%d/%s?" % (addr, resource), *args)

	def post_remote(self, addr, resource, data, *args):
		return self.post("nodes", data, "%d/%s?" % (addr, resource), *args)

def main():
	f = serial.Serial("/dev/ttyUSB0", 115200, timeout=10)
	vesna = ALHProtocolRemote(f)

	vesna.post_remote(7, "generator/program", 
			"in 1 sec for 1 sec with dev 0 conf 0 channel 0 power 0\r\n"
			"in 2 sec for 1 sec with dev 0 conf 0 channel 10 power 0\r\n"
			"in 3 sec for 1 sec with dev 0 conf 0 channel 20 power 0\r\n"
			"in 4 sec for 1 sec with dev 0 conf 0 channel 30 power 0\r\n"
	)

main()
