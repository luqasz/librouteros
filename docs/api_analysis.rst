============
Api analysis
============

This document aims to cover in depth analysis of routeros API. Lines that begin with ``--->`` represent data received from a device. Linet that start with ``<---`` represent data send to a device. End of sentence is marked with ``EOS``.

----------------
Succesfull login
----------------
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

--------------------
Failed login attempt
--------------------
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

-----------
Logging off
-----------
.. code-block:: none

    <--- /quit
    <--- EOS
    ---> !fatal
    ---> session terminated on request
    ---> EOS

------------------------
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

--------------
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
