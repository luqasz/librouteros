#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

'''
Command line interface for debugging purpouses.
'''


import logging
import getpass
from argparse import ArgumentParser
from sys import stdout, stdin
from select import select
from os import linesep

from librouteros import connect, LoginError, ConnError

argParser = ArgumentParser(description='mikrotik api cli interface')
argParser.add_argument('host', type=str, help="host to with to connect. may be fqdn, ipv4 or ipv6 address")
argParser.add_argument('-u', '--user', type=str, required=True, help="username")
argParser.add_argument('-p', '--port', type=int, default=8728, help="port to connect to (default 8728)")
args = argParser.parse_args()

mainlog = logging.getLogger('librouteros')
console = logging.StreamHandler(stdout)
mainlog.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(message)s')
console.setFormatter(formatter)
mainlog.addHandler(console)



def selectloop( api ):

    snt = []
    while True:
        sk = api.rwo.sock
        rwo = api.rwo

        rlist, wlist, errlist = select([sk, stdin], [], [], None)

        if sk in rlist:
            rwo.readSnt()

        if stdin in rlist:
            line = stdin.readline()
            line = line.split(linesep)
            line = line[0]
            if line:
                snt.append( line )
            elif not line and snt:
                rwo.writeSnt( tuple(snt) )
                snt = []

def main():
    pw = getpass.getpass()
    try:
        api = connect( args.host, args.user, pw, logger = mainlog )
    except ( LoginError, ConnError ) as err:
        exit(err)
    except KeyboardInterrupt:
        pass
    else:
        try:
            selectloop( api )
        except KeyboardInterrupt:
            pass
        except ConnError as e:
            print(e)
        finally:
            api.close()

if __name__ == '__main__':
    main()

