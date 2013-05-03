# -*- coding: utf-8 -*-
import signal
import sys
import os

dirname = os.path.abspath(sys.argv[0]).split('/bin/')[0]
var_directory = os.path.join(dirname, 'var')

if not os.path.isdir(var_directory):
    os.makedirs(var_directory)


def conveyor_server():
    from conveyor.server.__main__ import _main
    if '-c' not in sys.argv:
        sys.argv[1:1] = ['-c', 'conveyor-dev.conf']
    if 'stop' in sys.argv:
        pid = os.path.join(var_directory, 'conveyord.pid')
        if os.path.isfile(pid):
            with open(pid) as fd:
                pid = int(fd.read())
            os.kill(pid, signal.SIGINT)
        sys.exit(0)
    if 'start' not in sys.argv:
        sys.argv.extend(['--nofork', '-l', 'DEBUG'])
    sys.argv = [a for a in sys.argv if a not in ['start']]
    sys.exit(_main(sys.argv))


def conveyor_client():
    from conveyor.client.__main__ import _main
    if '-c' not in sys.argv:
        sys.argv[1:1] = ['-c', 'conveyor-dev.conf']
    sys.exit(_main(sys.argv))


def conveyor_print():
    input_file = os.path.abspath(sys.argv.pop())
    sys.argv[1:] = ['print', '--has-start-end', input_file]
    conveyor_client()
