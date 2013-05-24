# -*- coding: utf-8 -*-
import socket
import logging
import threading
import conveyor.client


class Cmd(conveyor.client._MethodCommand):

    _connection = None
    _log = logging.getLogger('client')

    def __init__(self, config_file, method, args, timeout=2.):
        self.method = method
        self.args = args
        self.timeout = timeout
        with open(config_file) as fp:
            dct = conveyor.json.load(fp)
        config = conveyor.config.Config(config_file, dct)
        address = config.get('common', 'address')
        address = conveyor.address.Address.address_factory(address)
        self.address = address
        self._jsonrpc = None
        self._stop = False
        self._code = 0
        self._result = None
        self._event_threads = []

    def _init_event_threads(self):
        eventqueue = conveyor.event.geteventqueue()
        for i in range(2):
            name = 'event_thread-%d' % (i,)
            thread = conveyor.event.EventQueueThread(eventqueue, name)
            thread.start()
            self._event_threads.append(thread)

    def _stop_event_threads(self):
        #self._log.error('end %s', self.method)
        conveyor.stoppable.StoppableManager.stopall()
        for thread in self._event_threads:
            if thread.is_alive():
                thread.join(1)

    def run(self):
        self._log.debug('running %s(%r)', self.method, self.args)
        try:
            if self._connection is None:
                self._connection = self.address.connect()
        except Exception, e:
            self._log.exception(e)
            pass
        else:
            self._connection._socket.settimeout(self.timeout)
            self._init_event_threads()
            self._jsonrpc = conveyor.jsonrpc.JsonRpc(
                self._connection, self._connection)
            hello_task = self._jsonrpc.request('hello', {})
            hello_task.stoppedevent.attach(
                self._guard_callback(self._hello_callback))
            hello_task.start()
            try:
                self._jsonrpc.run()
            except (Exception, socket.error) as e:
                self._log.exception(e)
                self._connection = None
                self._stop_event_threads()
            else:
                self._stop_event_threads()

        return self._code

    def _create_method_task(self):
        method_task = self._jsonrpc.request(self.method, self.args)
        return method_task

    def _method_callback(self, method_task):
        self._result = method_task.result
        self._stop_jsonrpc()


lock = threading.Lock()


def call(config_file, method, args={}, timeout=4):
    lock.acquire_lock(True)
    result = -1, None
    try:
        cmd = Cmd(config_file, method, args, timeout=timeout)
        cmd.run()
        result = cmd._code, cmd._result
    except (Exception, socket.timeout) as e:
        cmd._log.exception(e)
        cmd._connection = None
    lock.release()
    return result
