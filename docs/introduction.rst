Introduction
============


Features
--------

* Python type casting
* Key and values stored in dictionary
* Source address, port specification
* Logging support

Limitations
-----------

* No support for sentence tagging.
* No asynchronous support for reading/writing
* No TLS/SSL socket encryption
* No Diffie Hellman negotiation

Requirements
------------

* Python 2 or 3, with sufficiently recent versions of `pip` and `setuptools`
  * Verified working with `setuptools` version `34.1.1` and `pip` version `9.0.1`
* Mock 1.0.1 ( for runing unit tests ) or higher.
* nosetests3 for runing unit tests.

Unit tests
----------

This library comes with unit tests included. To run them:
::

    nosetests3 unit_tests/*
