#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""Command line interface for debugging purpouses."""

import logging
import getpass
from argparse import ArgumentParser
from sys import stdout, stdin
from select import select
from os import linesep

from librouteros import connect
from librouteros.exceptions import TrapError, FatalError

argParser = ArgumentParser(description="mikrotik api cli interface")
argParser.add_argument("host", type=str, help="host to with to connect. may be fqdn, ipv4 or ipv6 address")
argParser.add_argument("-u", "--user", type=str, required=True, help="username")
argParser.add_argument("-p", "--port", type=int, default=8728, help="port to connect to (default 8728)")
args = argParser.parse_args()

mainlog = logging.getLogger("librouteros")
console = logging.StreamHandler(stdout)
mainlog.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt="%(message)s")
console.setFormatter(formatter)
mainlog.addHandler(console)


def selectloop(api):
    snt = []
    while True:
        proto = api.protocol
        sk = proto.transport.sock

        rlist, wlist, errlist = select([sk, stdin], [], [], None)

        if sk in rlist:
            proto.readSentence()

        if stdin in rlist:
            line = stdin.readline()
            line = line.split(linesep)
            line = line[0]
            if line:
                snt.append(line)
            elif not line and snt:
                proto.writeSentence(snt[0], *snt[1:])
                snt = []


def main():
    pw = getpass.getpass()
    try:
        api = connect(args.host, args.user, pw, logger=mainlog)
    except (TrapError, ConnectionError) as err:
        exit(err)
    except KeyboardInterrupt:
        pass
    else:
        try:
            selectloop(api)
        except KeyboardInterrupt:
            pass
        except (ConnectionError, FatalError) as e:
            print(e)
        finally:
            api.close()


if __name__ == "__main__":
    main()
