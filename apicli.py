#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""Command line interface for debugging purpouses."""


import logging
import getpass
from argparse import ArgumentParser
from sys import stdout, stdin
from select import select
from os import linesep
import socket

from librouteros import login, ConnectionError, TrapError, FatalError

argParser = ArgumentParser(description='mikrotik api cli interface')
argParser.add_argument(
        'host', type=str,
        help="host to with to connect. may be fqdn, ipv4 or ipv6 address")
argParser.add_argument('-u', '--user', type=str, required=True, help="username")
argParser.add_argument(
        '-p', '--port', type=int, default=8728, help="port to connect to (default 8728)")
args = argParser.parse_args()

mainlog = logging.getLogger('librouteros')
console = logging.StreamHandler(stdout)
mainlog.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(message)s')
console.setFormatter(formatter)
mainlog.addHandler(console)


def selectloop(api, sk):
    snt = []
    while True:
        proto = api.protocol
        rlist, wlist, _ = select([sk, stdin], [], [], None)
        if sk in rlist:
            proto.readSentence()

        if stdin in rlist:
            line = stdin.readline().rstrip(linesep)
            if line:
                snt.append(line)
            elif not line and snt:
                proto.writeSentence(snt[0], *snt[1:])
                snt = []


def get_api():
    try:
        sk = socket.create_connection((args.host, args.port))
        api = login(args.user, getpass.getpass(), sock=sk)
        return api, sk
    except (TrapError, ConnectionError, socket.error, socket.timeout) as err:
        mainlog.error(err)
        exit(1)
    except KeyboardInterrupt:
        exit(0)


def main():
    api, sk = get_api()
    try:
        selectloop(api, sk)
    except KeyboardInterrupt:
        pass
    except (ConnectionError, FatalError) as e:
        print(e)
    finally:
        api.close()


if __name__ == '__main__':
    main()
