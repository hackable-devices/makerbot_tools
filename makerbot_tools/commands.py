# -*- coding: utf-8 -*-
from __future__ import (absolute_import, print_function, unicode_literals)

import sys

import logging

import conveyor.client
import conveyor.log
import conveyor.main

from conveyor.decorator import command
from makerbot_tools import client


@command(client.CancelCommand)
@command(client.ConnectCommand)
@command(client.CompatibleFirmware)
@command(client.DefaultConfigCommand)
@command(client.DirCommand)
@command(client.DisconnectCommand)
@command(client.DownloadFirmware)
@command(client.DriverCommand)
@command(client.DriversCommand)
@command(client.GetMachineVersions)
@command(client.GetUploadableMachines)
@command(client.JobCommand)
@command(client.JobsCommand)
@command(client.PauseCommand)
@command(client.PortsCommand)
@command(client.PrintCommand)
@command(client.PrintToFileCommand)
@command(client.PrintersCommand)
@command(client.ProfileCommand)
@command(client.ProfilesCommand)
@command(client.ReadEepromCommand)
@command(client.ResetToFactoryCommand)
@command(client.SliceCommand)
@command(client.UnpauseCommand)
@command(client.UploadFirmwareCommand)
@command(client.VerifyS3gCommand)
@command(client.WaitForServiceCommand)
@command(client.WriteEepromCommand)
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
