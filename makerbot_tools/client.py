# -*- coding: utf-8 -*-
import logging
import conveyor.client


class Cmd(conveyor.client._MethodCommand):

    def __init__(self, config_file, method, args):
        self.method = method
        self.args = args
        with open(config_file) as fp:
            dct = conveyor.json.load(fp)
        config = conveyor.config.Config(config_file, dct)
        address = config.get('common', 'address')
        address = conveyor.address.Address.address_factory(address)
        self.address = address
        self._log = logging.getLogger('cmd')
        self._jsonrpc = None
        self._stop = False
        self._code = 0
        self._result = None
        self._event_threads = []
        eventqueue = conveyor.event.geteventqueue()
        for i in range(2):
            name = 'event_thread-%d' % (i,)
            thread = conveyor.event.EventQueueThread(eventqueue, name)
            thread.start()
            self._event_threads.append(thread)

    def run(self):
        try:
            self._connection = self.address.connect()
        except Exception, e:
            self._log.exception(e)
            pass
        else:
            self._jsonrpc = conveyor.jsonrpc.JsonRpc(
                self._connection, self._connection)
            hello_task = self._jsonrpc.request('hello', {})
            hello_task.stoppedevent.attach(
                self._guard_callback(self._hello_callback))
            hello_task.start()
            self._jsonrpc.run()
        conveyor.stoppable.StoppableManager.stopall()
        for thread in self._event_threads:
            if thread.is_alive():
                thread.join(1)
        return self._code

    def _create_method_task(self):
        method_task = self._jsonrpc.request(self.method, self.args)
        return method_task

    def _method_callback(self, method_task):
        self._result = method_task.result
        self._stop_jsonrpc()

    def _init_event_threads(self):
        eventqueue = conveyor.event.geteventqueue()
        for i in range(1):
            name = 'event_thread-%d' % (i,)
            thread = conveyor.event.EventQueueThread(eventqueue, name)
            thread.start()
            self._event_threads.append(thread)


def call(config_file, method, args={}):
    cmd = Cmd(config_file, method, args)
    cmd.run()
    return cmd._code, cmd._result
