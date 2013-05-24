# -*- coding: utf-8 -*-
import socket
import logging
import threading
import conveyor.client


class Cmd(conveyor.client._MethodCommand):

    _log = logging.getLogger('client')
    _config_file = None
    _connection = None
    _timeout = None

    def __init__(self, config_file, method, args, timeout=2.):
        self.method = method
        self.args = args
        self._jsonrpc = None
        self._stop = False
        self._code = 0
        self._result = None
        self._event_threads = []
        self._init_class(config_file, timeout)

    @classmethod
    def _init_class(cls, config_file, timeout):
        cls.timeout = timeout
        cls.config_file = config_file

    def _init_event_threads(self):
        eventqueue = conveyor.event.geteventqueue()
        for i in range(2):
            name = 'event_thread-%d' % (i,)
            thread = conveyor.event.EventQueueThread(eventqueue, name)
            thread.start()
            self._event_threads.append(thread)

    def _stop_event_threads(self):
        conveyor.stoppable.StoppableManager.stopall()
        for thread in self._event_threads:
            if thread.is_alive():
                thread.join(1)

    @classmethod
    def _set_connection(cls):
        if cls._connection is not None:
            return cls._connection
        cls._log.warn('Get new connection')
        with open(cls._config_file) as fp:
            dct = conveyor.json.load(fp)
        config = conveyor.config.Config(cls._config_file, dct)
        address = config.get('common', 'address')
        address = conveyor.address.Address.address_factory(address)
        cls._connection = address.connect()
        cls._connection._socket.settimeout(cls._timeout)

    @classmethod
    def _reset_connection(cls):
        cls._connection = None

    def run(self):
        self._log.debug('running %s(%r)', self.method, self.args)
        try:
            self._set_connection()
        except Exception, e:
            self._log.exception(e)
        else:
            self._init_event_threads()
            self._jsonrpc = conveyor.jsonrpc.JsonRpc(
                self._connection, self._connection)
            hello_task = self._jsonrpc.request('hello', {})
            hello_task.stoppedevent.attach(
                self._guard_callback(self._hello_callback))
            hello_task.start()
            try:
                self._jsonrpc.run()
            except Exception as e:
                self._log.exception(e)
                self._reset_connection()
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
    cmd = Cmd(config_file, method, args, timeout=timeout)
    try:
        cmd.run()
        result = cmd._code, cmd._result
    except Exception as e:
        cmd._log.exception(e)
        cmd._connection = None
    lock.release()
    return result
