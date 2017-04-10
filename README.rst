.. vim:sw=3 ts=3 expandtab tw=78

Introduction
============

This package provides utilities and Python modules for managing VESNA-based
wireless sensor networks that are using the ALH protocol.

In a typical setup, VESNA nodes participate in a ZigBee-based wireless mesh
network. On this mesh network each sensor node exposes a HTTP-like interface,
supporting two types of requests: GET for state-less information retrieval
and POST for state-changing actions.

The ZigBee mesh is established by the coordinator. In addition to a ZigBee
interface, the coordinator also typically has an Ethernet adapter. At boot it
establishes a TCP/IP SSL tunnel and exposes an ALH service over it.

Usually, the SSL tunnel terminates in an infrastructure server that performs
the translation between ALH and a proper HTTP REST interface exposed on the
web::

   +------+
   | node | ALH -  ZigBee mesh
   +------+      \
                 |                    SSL tunnel
   +------+      |      +-------------+         +----------------+
   | node | ALH -+- ALH | coordinator | ALH --- | infrastructure | HTTPS -->
   +------+      |      +-------------+         +----------------+
                 |
   +------+      /
   | node | ALH -
   +------+

Alternatively, coordinator can also be directly connected to a client over a
serial line. This setup is typically used for development or debugging::

   +------+
   | node | ALH -  ZigBee mesh
   +------+      \
                 |                      serial line
   +------+      |      +-------------+
   | node | ALH -+- ALH | coordinator | ALH ------------------------------->
   +------+      |      +-------------+
                 |
   +------+      /
   | node | ALH -
   +------+

These tools transparently support both modes of operation. Typically either URL of the
HTTP REST endpoint is given or a character device for the serial line.


Installation
============

To install system-wide from the package index, run::

   $ pip install vesna-alhtools

This should also automatically install the required Python bindings for VESNA
spectrum sensor application. More information about it is at:
https://github.com/avian2/vesna-spectrum-sensor

To install system-wide from source, run::

   $ pip install .

To run tests::

   $ tox


Usage
=====

After installation, the following tools are available:

``alh-reprogram``
   Perform over-the-air reprogramming of the coordinator or sensor nodes.

``alh-map``
   Enumerate all the nodes participating in the sensor network by crawling the
   ZigBee mesh.

   Can be used for visualizing the network using Graphviz or network
   monitoring (via integration into Munin).

``alh-tx-test``
   Signal generator test.

``alh-endpoint-server``
   Simple ALH-to-HTTP endpoint server, useful for testing. It can be used
   instead of the proper infrastructure server.


Run each with ``--help`` as the only argument to get a list of available
options.

Note: if the API end-point is using basic authentication, you will be
prompted for credentials on the command line.

You can also save credentials into either a file named ``.alhrc`` in your
home directory or ``alhrc`` in the current directory. Format of the file is
as in the following example::

   Host example.com
   User <username>
   Password <password>
   # more Host, User, Password lines can follow

Several Python modules are installed as well. Refer to demo programs in the
demos/ directory for examples on how to use them. Classes and methods are
documented with docstring documentation. Some of it is accessible on-line
at https://vesna-alh-tools.readthedocs.io/en/latest/


Remote testing with rftest.py
=============================

This library provides a DeviceUnderTest class that is compatible with the
RF test utility from vesna-spectrum-sensor repository. It allows for testing of
radio hardware (e.g. SNE-ISMTV) using the production firmware (e.g.
NodeSpectrumSensor application) on a fully assembled node with minimal
additional wiring.

Testing setup looks like this::

   +----------+ coax +------+ zigbit +-------------+  SSL  +----------------+
   | R&S SMBV |----->| node |<-------| coordinator |<------| infrastructure |
   +----------+      +------+  ALH   +-------------+       +----------------+
         ^                                                           ^
         | usbtmc    +--------+  HTTPS                               |
         +-----------| rftest |--------------------------------------+
                     +--------+

Run rftest like this::

   $ vesna-rftest -i foo -R vesna.alh.rftest.RemoteDeviceUnderTest -O,-Uhttps://...,-u...,-n1


License
=======

Copyright (C) 2017 SensorLab, Jozef Stefan Institute
http://sensorlab.ijs.si

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Authors:	Tomaz Solc, <tomaz.solc@ijs.si>
