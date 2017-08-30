import binascii
import logging
import os
import re
import string
import sys
import time
import ssl
import requests
from functools import wraps

try:
	# Python 2.x
	from urlparse import urlparse
except ImportError:
	# Python 3.x
	from urllib.parse import urlparse
	import urllib3

	urllib3.disable_warnings()

log = logging.getLogger(__name__)

def cast_to_bytes(s):
	if isinstance(s, bytes):
		return s
	else:
		return s.encode('ascii')

def cast_args_to_bytes(method):
	@wraps(method)
	def method_wrapper(self, *args, **kwargs):
		args2 = [ cast_to_bytes(arg) for arg in args ]

		kwargs2 = {}
		for name, val in kwargs.items():
			kwargs2[name] = cast_to_bytes(val)

		return method(self, *args2, **kwargs2)

	return method_wrapper

class ALHResponse(object):
	"""This class represents the response of a resource handler.

	The ALH protocol does not define the encoding of strings passed thorugh
	it. It can be used for binary data as well. In practice however, most
	strings are 7-bit ASCII. Hence this class provides ASCII-decoded form
	of the response for convenience, as well as the undecoded binary.

	.. py:attribute:: text

	   Text form of the response (ASCII).

	.. py:attribute:: content

	   Binary form of the response (:py:class:`bytes` object on Python 3).
	"""
	def __init__(self, content):
		assert isinstance(content, bytes)
		self.text = content.decode('ascii', errors='replace').replace(u'\ufffd', '?')
		self.content = content

	def __str__(self):
		return self.text

	def __bytes__(Self):
		return self.content

	def __repr__(self):
		return "ALHResponse(%r)" % (self.content,)

class ALHException(Exception):
	"""Base class for errors related to the ALH protocol
	"""
	pass

class ALHProtocolException(ALHException):
	def __init__(self, msg):
		if msg.endswith(self.TERMINATOR):
			msg = msg[:-len(self.TERMINATOR)].strip()
		super(Exception, self).__init__(msg)

class JunkInput(ALHProtocolException):
	TERMINATOR = b"JUNK-INPUT\r\n"

class CorruptedData(ALHProtocolException): 
	TERMINATOR = b"CORRUPTED-DATA\r\n"

class ALHRandomError(ALHException): pass

class CRCError(ALHException): pass

class TerminalError(IOError): pass

class ALHProtocol:
	"""Base class for an ALH protocol service.

	This is an abstract class with some useful private methods.

	Implementations of this interface should override _get() and _post() methods.
	"""
	RETRIES = 5

	@cast_args_to_bytes
	def get(self, resource, *args):
		"""Issue a GET request to the service.

		Raises an ALHException in case of an error.

		:param resource: resource to issue request to
		:param args: arbitrary string arguments for the request

		:return: :py:class:`vesna.alh.ALHResponse` object
		"""
		rv = self._get(resource, *args)
		return ALHResponse(rv)

	@cast_args_to_bytes
	def post(self, resource, data, *args):
		"""Issue a POST request to the service

		Raises an ALHException in case of an error.

		:param resource: resource to issue request to
		:param data: POST data to attach to the request
		:param args: arbitrary string arguments for the request

		:return: :py:class:`vesna.alh.ALHResponse` object
		"""
		rv = self._post(resource, data, *args)
		return ALHResponse(rv)

	def _log_request(self, method, resource, args, data=None):
		msg = b"%s?%s" % (resource, b"".join(args))
		log.info("%8s: %s" % (method, msg.decode("ascii", "ignore")))

		if data is not None and len(data) > 4:
			if self._is_printable(data):
				data_ascii = data.decode("ascii", "ignore")
			else:
				data_ascii = "(unprintable)"
			log.info("    DATA: %s" % (data_ascii,))

	@staticmethod
	def _is_printable(resp):
		try:
			resp_ascii = resp.decode('ascii')
		except UnicodeDecodeError:
			return False

		return all(c in string.printable for c in resp_ascii)

	def _log_response(self, resp):
		if self._is_printable(resp):
			resp_ascii = resp.decode("ascii", "ignore").strip()
			log.info("response: %s" % (resp_ascii,))
		else:
			log.info("unprintable response (%d bytes)" % (len(resp),))

	def _send_with_retry(self, data):

		for retry in range(self.RETRIES):
			try:
				return self._send_with_error(data)
			except ALHException as e:
				if retry == self.RETRIES - 1:
					raise e
				else:
					log.exception("retrying (%d)" % (retry+1,))

	def _check_for_sneaky_error(self, resp):
		# This is extremely ugly. But since we don't have
		# currently any consistent way of specifying whether
		# a request failed or not, we check if the response
		# contains any strings that look like error messages.

		r = resp.decode('unicode_escape').lower()
		r = r.replace("bus errors  :", "")
		r = r.replace("   : 0 (error)", "")
		if "error" in r or "warning" in r:
			raise ALHRandomError(resp)


class ALHTerminal(ALHProtocol):
	"""ALH protocol implementation through a serial terminal.

	This implementation is used for testing and debugging when a sensor
	node is connected directly to a computer over a serial line.

	:param f: path to the character device of the terminal (usually an
	          instance of the :py:class:`serial.Serial` class)
	"""
	RESPONSE_TERMINATOR = b"\r\nOK\r\n"

	def __init__(self, f):
		self.f = f

	def _send(self, data):
		self.f.write(data)

		resp = b""
		while not resp.endswith(self.RESPONSE_TERMINATOR):
			d = self.f.read()
			if d:
				resp += d
			else:
				raise TerminalError

		return resp[:-len(self.RESPONSE_TERMINATOR)]

	def _recover(self):
		self._send(b"\r\n" * 5)

	def _crc(self, data):
		return binascii.crc32(data)

	def _send_with_error(self, data):
		resp = self._send(data)
		if resp.endswith(JunkInput.TERMINATOR):
			self._recover()
			raise JunkInput(resp)
		if resp.endswith(CorruptedData.TERMINATOR):
			raise CorruptedData(resp)

		self._check_for_sneaky_error(resp)
		self._log_response(resp)

		return resp

	def _get(self, resource, *args):
		self._log_request("GET", resource, args)

		arg = b"".join(args)
		return self._send_with_retry(b"get %s?%s\r\n" % (resource, arg))

	def _post(self, resource, data, *args):
		self._log_request("POST", resource, args, data)

		arg = b"".join(args)

		req = b"post %s?%s\r\nlength=%d\r\n%s\r\n" % (
				resource, arg, len(data), data)

		crc = self._crc(req)

		req += b"crc=%d\r\n" % crc

		return self._send_with_retry(req)

class ALHWeb(ALHProtocol):
	"""ALH protocol implementation through the HTTP infrastructure server.

	ALHWeb is typically used to access the coordinator of a ZigBee mesh network.

	If the API end-point is using basic authentication, you will be
	prompted for credentials on the command line.

	You can also save credentials into either a file named `.alhrc` in your
	home directory or `alhrc` in the current directory. Format of the file
	is as in the following example::

	    Host example.com
	    User <username>
	    Password <password>
	    # more Host, User, Password lines can follow

	:param base_url: base URL of the HTTP API (e.g. `https://crn.log-a-tec.eu/communicator`)
	:param cluster_id: numerical cluster id
	"""

	UA = "vesna-alh-tools/1.1"

	def __init__(self, base_url, cluster_id):
		self.base_url = base_url
		self.cluster_id = cluster_id

		o = urlparse(base_url)
		self.host = o.netloc

	def _get_passwd(self):

		paths = [
				'alhrc',
				'/etc/alhrc',
			]

		home = os.environ.get('HOME')
		if home is not None:
			paths.append(os.path.join(home, '.alhrc'))

		for path in paths:
			try:
				with open(path) as f:
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
							match = (value == self.host)
							user = None
							passwd = None
						elif match and (key == 'User'):
							user = value
						elif match and (key == 'Password'):
							passwd = value

						if match and user and passwd:
							return (user, passwd)

			except IOError:
				pass

		return None

	def _send(self, params):
		r = requests.get(	self.base_url,
					params=params,
					headers={'user-agent': self.UA},
					verify=False,
					auth=self._get_passwd(),
				)

		# Raise an exception if we got anything else than a 200 OK
		if r.status_code != 200:
			raise TerminalError(r.text)

		return r.content

	def _send_with_error(self, params):
		# loop until communication channel is free and our request
		# goes through.
		time_start = time.time()
		while True:
			resp = self._send(params)
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

		arg = b"".join(args)
		params = (
				('method', 'get'),
				('resource', b'%s?%s' % (resource, arg)),
				('cluster', str(self.cluster_id)),
		)

		return self._send_with_retry(params)

	def _post(self, resource, data, *args):
		self._log_request("POST", resource, args, data)

		arg = b"".join(args)
		params = (
				('method', 'post'),
				('resource', b'%s?%s' % (resource, arg)),
				('content', data),
				('cluster', str(self.cluster_id)),
		)

		return self._send_with_retry(params)

class ALHProxy(ALHProtocol):
	"""ALH protocol implementation through an ALH proxy.

	This implementation forwards arbitrary ALH requests through the "nodes"
	resource on an ALH service used as a proxy.

	ALHProxy is typically used to access nodes on the ZigBee mesh network behind
	the coordinator.

	:param alhproxy: ALH implementation used as a proxy
	:param addr: ZigBee address of the node to forward requests to
	"""
	def __init__(self, alhproxy, addr):
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
			response = self.alhproxy.get("nodes", b"%d/%s?" % (self.addr, resource), *args)
		except ALHRandomError as e:
			self._check_for_junk_state(str(e))
			raise

		return response.content

	def _post(self, resource, data, *args):
		try:
			response = self.alhproxy.post("nodes", data, b"%d/%s?" % (self.addr, resource), *args)
		except ALHRandomError as e:
			self._check_for_junk_state(str(e))
			raise

		# For POST requests, coordinator adds some string at the start
		# of the response.

		# Clean it up here, so that responses via proxy are identical
		# to responses with direct connection.
		content = re.sub(b"^Node #%d return;" % (self.addr,), b"", response.content)
		return content
