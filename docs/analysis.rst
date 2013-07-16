Routeros API analysis
======================

Unfortunatelly mikrotik `Wiki <http://wiki.mikrotik.com/wiki/API/>`_ page describing API lacks of detailed examples using api.

::

	<---
	
means bytes sent.

::

	--->
	
means bytes received.

Succesfull login
----------------

::

	<--- /login (6)
	<--- EOS
	---> !done (5)
	---> =ret=xxxxxxxxxxxxxxxxxxxxx (37)
	---> EOS
	<--- /login (6)
	<--- =name=admin (11)
	<--- =response=xxxxxxxxxxxxxxx (44)
	<--- EOS
	---> !done (5)
	---> EOS

	<--- /quit (5)
	<--- EOS
	---> !fatal (6)
	---> session terminated on request (29)
	---> EOS

Unsuccessful login
-------------------

::

	<--- /login (6)
	<--- EOS
	---> !done (5)
	---> =ret=xxxxxxxxxxxxxxxxxxxxx (37)
	---> EOS
	<--- /login (6)
	<--- =name=admin (11)
	<--- =response=xxxxxxxxxxxxxxxxxxxxx (44)
	<--- EOS
	---> !trap (5)
	---> =message=cannot log in (22)
	---> EOS
	---> !done (5)
	---> EOS

	<--- /quit (5)
	<--- EOS
	---> !fatal (6)
	---> session terminated on request (29)
	---> EOS
	

Fetch example
-------------

::

	<--- /tool/fetch (11)
	<--- =url=http://wp.pl/xxx (21)
	<--- .tag=3 (6)
	<--- EOS
	---> !re (3)
	---> =status=connecting (18)
	---> .tag=3 (6)
	---> EOS
	---> !re (3)
	---> =status=failed (14)
	---> .tag=3 (6)
	---> EOS
	---> !re (3)
	---> =status=failed (14)
	---> .tag=3 (6)
	---> EOS
	/cancel
	=tag=3
	.tag=7

	<--- /cancel (7)
	<--- =tag=3 (6)
	<--- .tag=7 (6)
	<--- EOS
	---> !trap (5)
	---> =category=2 (11)
	---> =message=interrupted (20)
	---> .tag=3 (6)
	---> EOS
	---> !done (5)
	---> .tag=7 (6)
	---> EOS
	---> !trap (5)
	---> =message=failure: 301 Moved Permanently (39)
	---> .tag=3 (6)
	---> EOS
	---> !done (5)
	---> .tag=3 (6)
	---> EOS
