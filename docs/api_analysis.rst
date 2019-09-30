Api analysis
============

This document aims to cover in depth analysis of routeros API. Lines that begin with ``--->`` represent data received from a device. Linet that start with ``<---`` represent data send to a device. End of sentence is marked with ``EOS``.

Succesfull login (pre 6.43)
---------------------------
.. code-block:: none

    <--- /login
    <--- EOS

    ---> !done
    ---> =ret=xxxxxxxxxxxxxxxxxxxxx
    ---> EOS

    <--- /login
    <--- =name=admin
    <--- =response=xxxxxxxxxxxxxxx
    <--- EOS

    ---> !done
    ---> EOS

Succesfull login (post 6.42)
----------------------------
.. code-block:: none

    <--- /login
    <--- =name=admin
    <--- =password=xxxxxxxxxxxxxxx
    <--- EOS

    ---> !done
    ---> EOS

Failed login attempt (pre 6.43)
-------------------------------
.. code-block:: none

    <--- /login
    <--- EOS

    ---> !done
    ---> =ret=xxxxxxxxxxxxxxxxxxxxx
    ---> EOS

    <--- /login
    <--- =name=admin
    <--- =response=xxxxxxxxxxxxxxxxxxxxx
    <--- EOS

    ---> !trap
    ---> =message=cannot log in
    ---> EOS
    ---> !done
    ---> EOS

Logging off
-----------
.. code-block:: none

    <--- /quit
    <--- EOS

    ---> !fatal
    ---> session terminated on request
    ---> EOS

Multiple empty responses
------------------------
.. code-block:: none

    <--- /ip/service/print
    <--- =.proplist=comment
    <--- EOS

    ---> !re
    ---> EOS
    ---> !re
    ---> EOS
    ---> !re
    ---> EOS
    ---> !re
    ---> EOS
    ---> !re
    ---> EOS
    ---> !re
    ---> EOS
    ---> !re
    ---> EOS
    ---> !done
    ---> EOS

Adding element
--------------
.. code-block:: none

    <--- /ip/address/add
    <--- =address=192.168.1.1/24
    <--- =interface=ether1
    <--- EOS

    ---> !done
    ---> =ret=*3
    ---> EOS

Canceling ``listen``
--------------------
Command returns ``!trap`` which is not actually any error at all:

.. code-block:: none

    <--- '/ip/address/listen'
    <--- '.tag=10'
    <--- EOS

    ---> '!re'
    ---> '.tag=10'
    ---> '=.id=*A'
    ---> '=address=1.1.1.1/32'
    ---> '=network=1.1.1.1'
    ---> '=interface=br-lan'
    ---> '=actual-interface=br-lan'
    ---> '=invalid=false'
    ---> '=dynamic=false'
    ---> '=disabled=false'
    ---> EOS
    ---> '!re'
    ---> '.tag=10'
    ---> '=.id=*A'
    ---> '=.dead=true'
    ---> EOS

    <--- '/cancel'
    <--- '=tag=10'
    <--- '.tag=20'
    <--- EOS

    ---> '!trap'
    ---> '.tag=10'
    ---> '=category=2'
    ---> '=message=interrupted'
    ---> EOS
    ---> '!done'
    ---> '.tag=20'
    ---> EOS
    ---> '!done'
    ---> '.tag=10'
    ---> EOS


Fetching from url
-----------------

.. code-block:: none

    <--- '/tool/fetch'
    <--- '=url=http://ping.online.net/10Mo.dat'
    <--- '.tag=1'
    <--- EOS

    ---> '!re'
    ---> '.tag=1'
    ---> '=status=connecting'
    ---> '=.section=0'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=731'
    ---> '=total=9765'
    ---> '=duration=1s'
    ---> '=.section=1'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=1579'
    ---> '=total=9765'
    ---> '=duration=2s'
    ---> '=.section=2'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=2427'
    ---> '=total=9765'
    ---> '=duration=3s'
    ---> '=.section=3'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=3275'
    ---> '=total=9765'
    ---> '=duration=4s'
    ---> '=.section=4'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=4139'
    ---> '=total=9765'
    ---> '=duration=5s'
    ---> '=.section=5'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=4987'
    ---> '=total=9765'
    ---> '=duration=6s'
    ---> '=.section=6'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=5839'
    ---> '=total=9765'
    ---> '=duration=7s'
    ---> '=.section=7'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=6687'
    ---> '=total=9765'
    ---> '=duration=8s'
    ---> '=.section=8'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=7551'
    ---> '=total=9765'
    ---> '=duration=9s'
    ---> '=.section=9'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=8415'
    ---> '=total=9765'
    ---> '=duration=10s'
    ---> '=.section=10'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=9279'
    ---> '=total=9765'
    ---> '=duration=12s'
    ---> '=.section=11'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=finished'
    ---> '=downloaded=9765'
    ---> '=total=9765'
    ---> '=duration=13s'
    ---> '=.section=12'
    ---> EOS
    ---> '!done'
    ---> '.tag=1'
    ---> EOS

Canceling fetch
---------------

.. code-block:: none

    <--- '/tool/fetch'
    <--- '=url=http://ping.online.net/10Mo.dat'
    <--- '.tag=1'
    <--- EOS

    ---> '!re'
    ---> '.tag=1'
    ---> '=status=connecting'
    ---> '=.section=0'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=18'
    ---> '=total=9765'
    ---> '=duration=0s'
    ---> '=.section=1'
    ---> EOS
    ---> '!re'
    ---> '.tag=1'
    ---> '=status=downloading'
    ---> '=downloaded=853'
    ---> '=total=9765'
    ---> '=duration=1s'
    ---> '=.section=2'
    ---> EOS

    <--- '/cancel'
    <--- '=tag=1'
    <--- EOS
    ---> '!trap'
    ---> '.tag=1'
    ---> '=category=2'
    ---> '=message=interrupted'
    ---> EOS
    ---> '!done'
    ---> EOS
    ---> '!done'
    ---> '.tag=1'
    ---> EOS
