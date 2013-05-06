#!/usr/bin/python

import sys
from execute import execute

def push():
    execute('tx push -s')

def pull():
    execute('tx pull')


if __name__ == '__main__':
    if len(sys.argv)<2:
        raise Exception("missing argument: push or pull")
    arg = sys.argv[1]
    if arg == 'push':
        push()
    elif arg == 'pull':
        pull()
    else:
        raise Exception("unknown argument: (%s)" % arg)
        
