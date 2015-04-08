import binascii
import logging
import os
import re
import string
import sys
import time
import urllib
import ssl

log = logging.getLogger(__name__)

class ALHException(Exception): pass

class ALHProtocolException(ALHException):
	def __init__(self, msg):
		if msg.endswith(self.TERMINATOR):
			msg = msg[:-len(self.TERMINATOR)].strip()
		super(Exception, self).__init__(msg)

class JunkInput(ALHProtocolException):
	TERMINATOR = "JUNK-INPUT\r\n"

class CorruptedData(ALHProtocolException): 
	TERMINATOR = "CORRUPTED-DATA\r\n"

class ALHRandomError(ALHException): pass

class CRCError(ALHException): pass

class TerminalError(IOError): pass

class ALHURLOpener(urllib.FancyURLopener):
	version = "vesna-alh-tools/1.0"

	def __init__(self):
		try:
			context = ssl._create_unverified_context()
		except AttributeError:
			context = None

		urllib.FancyURLopener.__init__(self, context=context)

	def prompt_user_passwd(self, host, realm):

		paths = [
				'alhrc',
				'/etc/alhrc',
			]

		home = os.environ.get('HOME')
		if home is not None:
			paths.append(os.path.join(home, '.alhrc'))

		for path in paths:
			try:
				f = open(path)
			except IOError:
				continue

			match = False
			user = None
			passwd = None

			for line in f:
				if line.startswith('#'):
					continue

				try:
					key, value = line.strip().split()
				except ValueError:
					continue

				if (key == 'Host'):
					match = (value == host)
					user = None
					passwd = None
				elif match and (key == 'User'):
					user = value
				elif match and (key == 'Password'):
					passwd = value

				if match and user and passwd:
					return (user, passwd)

		return urllib.FancyURLopener.prompt_user_passwd(self, host, realm)

urllib._urlopener = ALHURLOpener()

class ALHProtocol:
	"""Base class for an ALH protocol service.

	This is an abstract class with some useful private methods.

	Implementations of this interface should override _get() and _post() methods.
	"""
	RETRIES = 5

	def get(self, resource, *args):
		"""Issue a GET request to the service.

		Returns the string reply from the resource handler or raises an
		ALHException in case of an error.

		resource -- resource to issue request to
		args -- arbitrary string arguments for the request.
		"""
		return self._get(resource, *args)

	def post(self, resource, data, *args):
		"""Issue a POST request to the service

		Returns the string reply from the resource handler or raises an
		ALHException in case of an error.

		resource -- resource to issue request to
		data -- POST data to attach to the request
		args -- arbitrary string arguments for the request
		"""
		return self._post(resource, data, *args)

	def _log_request(self, method, resource, args, data=None):
		log.info("%8s: %s?%s" % (method, resource, "".join(args)))
		if data is not None and len(data) > 4 and all(c in string.printable for c in data):
			log.info("    DATA: %s" % (data,))

	def _log_response(self, resp):
		if all(c in string.printable for c in resp):
			resp_ascii = resp.strip().decode("ascii", "ignore")
			log.info("response: %s" % (resp_ascii,))
		else:
			log.info("unprintable response (%d bytes)" % (len(resp),))

	def _send_with_retry(self, data):

		for retry in xrange(self.RETRIES):
			try:
				return self._send_with_error(data)
			except ALHException, e:
				if retry == self.RETRIES - 1:
					raise e
				else:
					log.exception("retrying (%d)" % (retry+1,))

	def _check_for_sneaky_error(self, resp):
		# This is extremely ugly. But since we don't have
		# currently any consistent way of specifying whether
		# a request failed or not, we check if the response
		# contains any strings that look like error messages.

		r = resp.lower()
		r = r.replace("bus errors  :", "")
		r = r.replace("   : 0 (error)", "")
		if "error" in r or "warning" in r:
			raise ALHRandomError(resp)


class ALHTerminal(ALHProtocol):
	"""ALH protocol implementation through a serial terminal."""
	RESPONSE_TERMINATOR = "\r\nOK\r\n"

	def __init__(self, f):
		"""Create a new ALHTerminal object.

		f -- Path to the character device of the terminal
		"""
		self.f = f

	def _send(self, data):
		self.f.write(data)

		resp = ""
		while not resp.endswith(self.RESPONSE_TERMINATOR):
			d = self.f.read()
			if d:
				resp += d
			else:
				raise TerminalError

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

		self._check_for_sneaky_error(resp)
		self._log_response(resp)

		return resp

	def _get(self, resource, *args):
		self._log_request("GET", resource, args)

		arg = "".join(args)
		return self._send_with_retry("get %s?%s\r\n" % (resource, arg))

	def _post(self, resource, data, *args):
		self._log_request("POST", resource, args, data)

		arg = "".join(args)

		req = "post %s?%s\r\nlength=%d\r\n%s\r\n" % (
				resource, arg, len(data), data)

		crc = self._crc(req)

		req += "crc=%d\r\n" % crc

		return self._send_with_retry(req)

class ALHWeb(ALHProtocol):
	"""ALH protocol implementation through the HTTP infrastructure server."""

	def __init__(self, base_url, cluster_id):
		"""Create a new ALHWeb object.

		Note: if the API end-point is using basic authentication, you will be
		prompted for credentials on the command line.

		You can also save credentials into either a file named ".alhrc" in your home
		directory or "alhrc" in the current directory. Format of the file is as in
		the following example:

		Host example.com
		User <username>
		Password <password>
		# more Host, User, Password lines can follow

		base_url -- Base URL of the HTTP API (e.g. https://crn.log-a-tec.eu/communicator)
		cluster_id -- Numerical cluster id
		"""
		self.base_url = base_url
		self.cluster_id = cluster_id

	def _send(self, url):
		f = urllib.urlopen(url)
		resp = f.read()

		# Raise an exception if we got anything else than a 200 OK
		if f.getcode() != 200:
			raise TerminalError(resp)

		return resp

	def _send_with_error(self, url):
		# loop until communication channel is free and our request
		# goes through.
		time_start = time.time()
		while True:
			resp = self._send(url)
			if resp != "ERROR: Communication in progress":
				break

			log.info("communicator is busy (have been waiting for %d s)" %
					(time.time() - time_start))

			time.sleep(1)

		self._check_for_sneaky_error(resp)
		
		self._log_response(resp)
		return resp

	def _get(self, resource, *args):
		self._log_request("GET", resource, args)

		arg = "".join(args)
		query = (
				('method', 'get'),
				('resource', '%s?%s' % (resource, arg)),
				('cluster', str(self.cluster_id)),
		)

		url = "%s?%s" % (self.base_url, urllib.urlencode(query))

		return self._send_with_retry(url)

	def _post(self, resource, data, *args):
		self._log_request("POST", resource, args, data)

		arg = "".join(args)
		query = (
				('method', 'post'),
				('resource', '%s?%s' % (resource, arg)),
				('content', '%s' % (data,)),
				('cluster', str(self.cluster_id)),
		)

		url = "%s?%s" % (self.base_url, urllib.urlencode(query))

		return self._send_with_retry(url)

class ALHProxy(ALHProtocol):
	"""ALH protocol implementation through an ALH proxy.

	This implementation forwards arbitrary ALH requests through the "nodes"
	resource on an ALH service used as a proxy.

	Proxy is typically used to access nodes on the ZigBee mesh network behind
	the coordinator.
	"""
	def __init__(self, alhproxy, addr):
		"""Create a new ALHProxy object.

		alhproxy -- ALH implementation used as a proxy
		addr -- ZigBee address of the node to forward requests to
		"""
		self.alhproxy = alhproxy
		self.addr = addr

	def _recover_remote(self):
		self.alhproxy.post("radio/noderesetparser", "1", "%d" % (self.addr,))

	def _check_for_junk_state(self, message):
		g = re.search("NODES:Node ([0-9]+) parser is in junk state\r\nERROR", message)
		if g:
			assert(int(g.group(1)) == self.addr)
			self._recover_remote()

	def _get(self, resource, *args):
		try:
			return self.alhproxy.get("nodes", "%d/%s?" % (self.addr, resource), *args)
		except ALHRandomError, e:
			self._check_for_junk_state(str(e))
			raise

	def _post(self, resource, data, *args):
		try:
			response = self.alhproxy.post("nodes", data, "%d/%s?" % (self.addr, resource), *args)
		except ALHRandomError, e:
			self._check_for_junk_state(str(e))
			raise

		# For POST requests, coordinator adds some string at the start
		# of the response.

		# Clean it up here, so that responses via proxy are identical
		# to responses with direct connection.
		response = re.sub("^Node #%d return;" % (self.addr,), "", response)
		return response
