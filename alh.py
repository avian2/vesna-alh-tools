import binascii
import re
import urllib

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

class CRCError(Exception): pass

"""Almost-like-HTTP protocol handler
"""
class ALHProtocol:
	pass

class ALHTerminal(ALHProtocol):
	RESPONSE_TERMINATOR = "\r\nOK\r\n"

	def __init__(self, f):
		self.f = f

	def _log(self, msg):
		pass

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

		self._log(resp)
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

class ALHWeb(ALHProtocol):
	def __init__(self, base_url):
		self.base_url = base_url

	def _log(self, msg):
		pass

	def _send(self, url):
		resp = urllib.urlopen(url).read()
		#resp = resp.replace("<br>", "\n")
		return resp

	def _send_with_error(self, url):
		resp = self._send(url)

		# this usually, but not always, means something went
		# wrong.
		if "error" in resp.lower() or "warning" in resp.lower():
			raise ALHRandomError(resp)
		
		self._log(resp)
		return resp

	def get(self, resource, *args):

		arg = "".join(args)
		query = (
				('method', 'get'),
				('resource', '%s?%s' % (resource, arg)),
		)

		url = "%s?%s" % (self.base_url, urllib.urlencode(query))

		return self._send_with_error(url)

	def post(self, resource, data, *args):

		arg = "".join(args)
		query = (
				('method', 'post'),
				('resource', '%s?%s' % (resource, arg)),
				('content', '%s' % (data,)),
		)

		url = "%s?%s" % (self.base_url, urllib.urlencode(query))

		return self._send_with_error(url)

class ALHProxy(ALHProtocol):
	def __init__(self, alhproxy, addr):
		self.alhproxy = alhproxy
		self.addr = addr

	def _recover_remote(self):
		self.alhproxy.post("radio/noderesetparser", "", "%d" % (self.addr,))

	def _check_for_junk_state(self, message):
		g = re.search("NODES:Node ([0-9]+) parser is in junk state\r\nERROR", message)
		if g:
			assert(int(g.group(1)) == self.addr)
			self._recover_remote()

	def get(self, resource, *args):
		try:
			return self.alhproxy.get("nodes", "%d/%s?" % (self.addr, resource), *args)
		except ALHRandomError, e:
			self._check_for_junk_state(str(e))
			raise

	def post(self, resource, data, *args):
		try:
			return self.alhproxy.post("nodes", data, "%d/%s?" % (self.addr, resource), *args)
		except ALHRandomError, e:
			self._check_for_junk_state(str(e))
			raise

