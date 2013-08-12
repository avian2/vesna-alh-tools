#!/usr/bin/python

from distutils.core import Command, setup
import unittest

UNITTESTS = [
		"cdf",
		"alh",
	]

class TestCommand(Command):
	user_options = [ ]

	def initialize_options(self):
		pass

	def finalize_options(self):
		pass

	def run(self):
		suite = unittest.TestSuite()

		suite.addTests(
			unittest.defaultTestLoader.loadTestsFromNames(
				"tests." + test for test in UNITTESTS) )

		result = unittest.TextTestRunner(verbosity=2).run(suite)


setup(name='vesna-alhtools',
      version='0.1',
      description='Tools for talking the VESNA almost-like-HTTP protocol',
      license='GPL',
      long_description=open("README").read(),
      author='Tomaz Solc',
      author_email='tomaz.solc@tablix.org',

      packages = [ 'vesna/alh', 'vesna/cdf' ],
      scripts = [ 'scripts/alh-reprogram',
	      'scripts/alh-map',
	      'scripts/alh-tx-test',
	      'scripts/alh-endpoint-server',
	      'scripts/alh-measure-rssi' ],

      requires = [ 'vesna' ],
      provides = [ 'vesna.alh', 'vesna.cdf' ],

      cmdclass = { 'test': TestCommand },
)
