#!/usr/bin/python

import os
from setuptools import setup

def get_long_description():
	return open(os.path.join(os.path.dirname(__file__), "README.rst")).read()

setup(name='vesna-alhtools',
      version='1.0.5',
      description='Tools for talking the VESNA almost-like-HTTP protocol',
      license='GPL',
      long_description=get_long_description(),
      author='Tomaz Solc',
      author_email='tomaz.solc@ijs.si',
      url='https://github.com/avian2/vesna-alh-tools',

      packages = [ 'vesna', 'vesna.alh', 'vesna.cdf' ],

      namespace_packages = [ 'vesna' ],

      scripts = [ 'scripts/alh-reprogram',
	      'scripts/alh-map',
	      'scripts/alh-tx-test',
	      'scripts/alh-endpoint-server',
	      'scripts/alh-measure-rssi' ],

      install_requires = [ 'vesna-spectrumsensor', 'numpy', 'python-dateutil', 'lxml', 'requests' ],

      test_suite = 'test',
)
