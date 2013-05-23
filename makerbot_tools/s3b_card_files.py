# -*- coding: utf-8 -*-
import os
import sys
import time
import makerbot_driver
import optparse
import logging


logging.basicConfig(stream=sys.stderr, level=logging.INFO)
log = logging.getLogger('s3b')


def main():
    parser = optparse.OptionParser()
    parser.add_option(
        "-m", "--machine", dest="machine",
        help="machine type to scan for, example ReplicatorSingle",
        default="The Replicator 2")
    parser.add_option(
        "-p", "--port", dest="port",
        help="The port you want to connect to (OPTIONAL)",
        default=None)
    parser.add_option(
        "-s", "--sequences", dest="sequences",
        help="Flag to not use makerbot_driver's start/end sequences",
        default=False, action="store_true")

    (options, args) = parser.parse_args()

    if options.port is None:
        md = makerbot_driver.MachineDetector()
        md.scan(options.machine)
        port = md.get_first_machine()
        if port is None:
            print "Can't Find %s" % (options.machine)
            sys.exit()
    else:
        port = options.port
    factory = makerbot_driver.MachineFactory()
    obj = factory.build_from_port(port)

    reset = True
    filenames = []
    filename = True
    while filename:
        filename = str(obj.s3g.get_next_filename(reset)[:-1])
        reset = False
        if filename:
            filenames.append(filename)
    print(filenames)

