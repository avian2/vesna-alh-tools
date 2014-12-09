#!/usr/bin/python

from setuptools import setup

setup(name='vesna-alhtools',
      version='0.1',
      description='Tools for talking the VESNA almost-like-HTTP protocol',
      license='GPL',
      long_description=open("README").read(),
      author='Tomaz Solc',
      author_email='tomaz.solc@tablix.org',

      packages = [ 'vesna', 'vesna.alh', 'vesna.cdf' ],

      namespace_packages = [ 'vesna' ],

      scripts = [ 'scripts/alh-reprogram',
	      'scripts/alh-map',
	      'scripts/alh-tx-test',
	      'scripts/alh-endpoint-server',
	      'scripts/alh-measure-rssi' ],

      requires = [ 'vesna' ],
      provides = [ 'vesna.alh', 'vesna.cdf' ],

      test_suite = 'tests',
)
