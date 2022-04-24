SmartGrid
=========

SmartGrid is a Python library that provides a set of functions for simulating the performance of PV systems.
The library `smartgrid` is composed of several modules:

- image_processing: set of functions to load satellite images, process them and compute block matching and GHI models.
- io: set of functions to export time series data to the Grafana dashboard tool
- microgrid: code for hypbrid PV system performance simulation (with inverter and battery components)
- pvmodeling: simulation of PV system

All this code is tested and documented using docstrings. The unit tests are a good start to understand modules API.
Unit tests are in the folder `smartgrid/tests`.

Acceptance tests are in the folder `acceptance_tests/notebooks` written as Python Notebooks.
These notebooks are also exported in this documentation in the folder `tutorial`.

Quick start
-----------

Clone the GIT repository:

.. code-block:: bash

    git clone smartgridrepo.git

Install the dependencies (python conda and pip):

.. code-block:: bash

   make install

Start all the tests (unit tests and acceptance):

.. code-block:: bash

    make test

Docker
------

Docker is used for the smartgrid deployment. Docker technlology encapsulate all the installation, initialization and
deployment steps of the smartgrid project.
Starting all the applications is easy with the following command (docker and docker-compose installation is required).

.. code-block:: bash

   docker-compose up -d

Contents
--------

.. toctree::
   :maxdepth: 2

   modules
   tutorial

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`

