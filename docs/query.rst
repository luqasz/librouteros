Query
=====

Basic usage
-----------
Get only ``name`` and ``disabled`` keys from all interfaces.

.. code-block:: python

   from librouteros.query import Key
   # Each key must be created first in order to reference it later.
   name = Key('name')
   disabled = Key('disabled')

   for row in api.path('/interface').select(name, disabled):
      print(row)

Advanced Usage
--------------
Adding ``where()``, allows to fine tune search criteria.
Syntax is very simmilar to a SQL query.

.. code-block:: python

   name = Key('name')
   disabled = Key('disabled')
   query = api.path('/interface').select(name, disabled).where(
           disabled == False,
           Or(
               name == 'ether2',
               name == 'wlan-lan',
               ),
           )

Above code demonstrates how to select ``name``, ``disabled`` fields where each interface is disabled
and ``name`` is equal to one of ``ether2``, ``wlan-lan``.
If you do not specify any logical operation within `where()`, them it defaults to `And()`.
Above example can be rewritten using `In` operator.

.. code-block:: python

   name = Key('name')
   disabled = Key('disabled')
   query = api.path('/interface').select(name, disabled).where(
           disabled == False,
           name.In('ether2', 'wlan-lan'),
           )

Usable operators
----------------
======== =========
operator example
======== =========
``==``   ``name == 'ether2'``
``!=``   ``name != 'ether2'``
``>``    ``mtu > 1500``
``<``    ``mtu < 1400``
``In``   ``name.In('ether1', 'ether2', 'wlan1')``
======== =========


Logical operators
-----------------
``And``, ``Or``. Each operator takes at least two expressions and performs a logical operation translating it to API
query equivalents.
