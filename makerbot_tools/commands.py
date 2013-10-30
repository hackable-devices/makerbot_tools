# -*- coding: utf-8 -*-
from __future__ import (absolute_import, print_function, unicode_literals)

import sys

import logging

import conveyor.client
import conveyor.log
import conveyor.main

from conveyor.decorator import command


@command(conveyor.client.CancelCommand)
@command(conveyor.client.ConnectCommand)
@command(conveyor.client.CompatibleFirmware)
@command(conveyor.client.DefaultConfigCommand)
@command(conveyor.client.DirCommand)
@command(conveyor.client.DisconnectCommand)
@command(conveyor.client.DownloadFirmware)
@command(conveyor.client.DriverCommand)
@command(conveyor.client.DriversCommand)
@command(conveyor.client.GetMachineVersions)
@command(conveyor.client.GetUploadableMachines)
@command(conveyor.client.JobCommand)
@command(conveyor.client.JobsCommand)
@command(conveyor.client.PauseCommand)
@command(conveyor.client.PortsCommand)
@command(conveyor.client.PrintCommand)
@command(conveyor.client.PrintToFileCommand)
@command(conveyor.client.PrintersCommand)
@command(conveyor.client.ProfileCommand)
@command(conveyor.client.ProfilesCommand)
@command(conveyor.client.ReadEepromCommand)
@command(conveyor.client.ResetToFactoryCommand)
@command(conveyor.client.SliceCommand)
@command(conveyor.client.UnpauseCommand)
@command(conveyor.client.UploadFirmwareCommand)
@command(conveyor.client.VerifyS3gCommand)
@command(conveyor.client.WaitForServiceCommand)
@command(conveyor.client.WriteEepromCommand)
@command(conveyor.client.GetExtendedPositionCommand) #CKAB code here
class ClientMain(conveyor.main.AbstractMain):
    _program_name = 'conveyor'

    _config_section = 'client'

    _logging_handlers = ['stderr']

    def _run(self):
        self._log_startup(logging.DEBUG)
        self._init_event_threads()
        command = self._parsed_args.command_class(
            self._parsed_args, self._config)
        code = command.run()
        return code


def _main(argv):  # pragma: no cover
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    main = ClientMain()
    code = main.main(argv)
    return code
