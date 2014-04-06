# -*- coding: UTF-8 -*-

from os import linesep
from re import compile, search
from subprocess import Popen, PIPE

def on_master( branches ):
    '''
    check if on branch master.

    branches
        iterable
    '''
    regexp = compile(r'^\* master')
    results = filter( regexp.search, branches )
    list(results)

    return True if len(branches) == 1 else False


def get_branches():
    '''
    get branches from git
    '''

    p = Popen(['git', 'branch', '--no-color'],
                stdout=PIPE, stderr=PIPE)
    p.stderr.close()
    lines = p.stdout.readlines()
    lines = list( line.decode('UTF-8') for line in lines )

    return lines


def get_version():
    '''
    get version from git describe
    '''

    p = Popen(['git', 'describe', '--tags'],
                stdout=PIPE, stderr=PIPE)
    p.stderr.close()
    line = p.stdout.readlines()[0]
    line = line.decode('UTF-8')

    #remove linesep from end of string
    return line.split(linesep)[0]


def stable_version( version ):
    '''
    check if passed version is of stable release
    eg. 1.0, 1.1 etc.
    '''

    return search('^\d+\.\d+$',version)
