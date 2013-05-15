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
        "-f", "--filename", dest="filename",
        help="gcode file to print", default=False)
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

    assembler = makerbot_driver.GcodeAssembler(getattr(obj, 'profile'))
    start, end, variables = assembler.assemble_recipe()
    start_gcode = assembler.assemble_start_sequence(start)
    end_gcode = assembler.assemble_end_sequence(end)

    filename = os.path.basename(options.filename)
    filename = os.path.splitext(filename)[0]

    parser = getattr(obj, 'gcodeparser')
    parser.environment.update(variables)
    parser.state.values["build_name"] = filename[:15]

    log.info('Using %s on %s with %s', factory, port, variables)

    def exec_line(line):
        while True:
            try:
                parser.execute_line(line)
                break
            except makerbot_driver.BufferOverflowError:
                try:
                    parser.s3g.writer._condition.wait(.2)
                except RuntimeError:
                    time.sleep(.2)

    if options.sequences:
        for line in start_gcode:
            exec_line(line)
    with open(options.filename) as f:
        for line in f:
            exec_line(line)
    if options.sequences:
        for line in end_gcode:
            exec_line(line)
