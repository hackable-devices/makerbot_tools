# -*- coding: utf-8 -*-
from makerbot_tools.client import call
from makerbot_tools.crontab import Crontab
import subprocess
import bottle
import time
import glob
import os
import zmq
from random import randint

upload_dir = os.path.expanduser('~/gcodes')
try:
    os.makedirs(upload_dir)
except OSError:
    # dir exist
    pass

dirname = os.path.abspath(os.path.dirname(__file__))

client = os.path.join(
    os.path.dirname(dirname),
    'bin', 'conveyor-client')

printer = os.path.join(
    os.path.dirname(dirname),
    'bin', 'print')

config = os.path.join(
    os.path.dirname(dirname),
    'conveyor-dev.conf')

bottle.TEMPLATE_PATH.append(
    os.path.join(dirname, 'views')
)
static_root = os.path.join(dirname, 'static')


def call_client(method, args=None):
    if args is None:
        args = {}
    method = {
        'printers': 'getprinters',
        'ports': 'getports',
        'jobs': 'getjobs',
        'position': 'extendedposition',
        'pause': 'pause',
    }.get(method, method)
    if method == 'connect':
        args = {
            'machine_name': None,
            'port_name': None,
            'driver_name': None,
            'profile_name': None,
            'persistent': False,
        }
    code, data = call(config, method, args)
    if code == 0:
        data = dict(success=True, result=data)
    else:
        data = dict(success=False)
    return data


def client_response(*args):
    def req():
        return call_client(*args)
    return req

for cmd in ('printers', 'profiles', 'jobs', 'drivers'):
    bottle.get('/api/' + cmd, callback=client_response(cmd))

for cmd in ('connect', 'disconnect'):
    bottle.get('/api/' + cmd, callback=client_response(cmd))


def ng(value):
    return '{{ %s }}' % value


@bottle.get('/')
@bottle.view('index')
def index():
    return {'ng': ng}


@bottle.get('/crons')
@bottle.view('cron')
def crons():
    filenames = []
    for filename in sorted(glob.glob(os.path.join(upload_dir, '*.gcode'))):
        basename = os.path.basename(filename)
        filenames.append(basename)

    crontab = Crontab(printer)
    crontab.read()

    return {'ng': ng, 'crontab': crontab, 'filenames': filenames}


#@bottle.get('/test')   #to test makerbot commands directly trough the browser
#def test():
    #cmd = [printer, os.path.join(upload_dir, filename)]
    #p = subprocess.Popen(cmd) #, close_fds=True)
    #time.sleep(1)
    #args = {'machine_name': printer,}
    #data = call_client('position', args)
    #return data


    
@bottle.get('/printviewer')
@bottle.view('printviewer.html')
def printviewer():
    context = zmq.Context()
    #  Socket to talk to server
    socket = context.socket(zmq.REQ)
    socket.connect ("tcp://localhost:5555")
    
    #  Do 1 request and wait for a response
    socket.send ("preview")
    #  Get the reply.
    message = socket.recv() #maybe do something with it later ? For now it stops function from finishing execution so that the retrieved image is the right one.
    msglist = message.split("+")
    truc = msglist[0]
    machin = msglist[1]
       
    #bottle.redirect('/printviewer') #a link was used instead of the redirect since all we want is the image to be refresed, no need for python
    return {'ng': ng, "file": truc, "status": machin}   
    

    
@bottle.get('/apsetupconfirm')
@bottle.view('apsetupconfirm.html')
def apsetup():
    return {'ng': ng}   
    
    
@bottle.get('/apsetup')
@bottle.view('apsetup.html')
def apsetup():
    context = zmq.Context()
    #  Socket to talk to server
    socket = context.socket(zmq.REQ)
    socket.connect ("tcp://localhost:5555")
    
    #  Do 1 request and wait for a response
    socket.send ("configureartefact")
    #  Get the reply.
    message = socket.recv() #maybe do something with it later ? For now it stops function from finishing execution so that the retrieved image is the right one.
       
    #bottle.redirect('/printviewer') #a link was used instead of the redirect since all we want is the image to be refresed, no need for python
    return {'ng': ng, "file": message}   


@bottle.get('/startapcheck')
def startapcheck():
    context = zmq.Context()
    #  Socket to talk to server
    socket = context.socket(zmq.REQ)
    socket.connect ("tcp://localhost:5555")
    
    #  Do 1 request and wait for a response
    socket.send ("startapcheck")
    #  Get the reply.
    message = socket.recv() #maybe do something with it later ? For now it stops function from finishing execution so that the retrieved image is the right one.
       
    bottle.redirect('/printviewer')
    
    
@bottle.get('/stopapcheck')
def stopapcheck():
    context = zmq.Context()
    #  Socket to talk to server
    socket = context.socket(zmq.REQ)
    socket.connect ("tcp://localhost:5555")
    
    #  Do 1 request and wait for a response
    socket.send ("stopapcheck")
    #  Get the reply.
    message = socket.recv() #maybe do something with it later ? For now it stops function from finishing execution so that the retrieved image is the right one.
       
    bottle.redirect('/printviewer')
    
    
    
#@bottle.get('/apsetup')
#@bottle.view('apsetup.html')
#def printviewer():
#    context = zmq.Context()
    #  Socket to talk to server
#    socket = context.socket(zmq.REQ)
#    socket.connect ("tcp://localhost:5555")
    
    #  Do 1 request and wait for a response
#    socket.send ("configureartefact")
    #  Get the reply.
#    message = socket.recv() #maybe do something with it later ? For now it stops function from finishing execution so that the retrieved image is the right one.
       
    #bottle.redirect('/printviewer') #a link was used instead of the redirect since all we want is the image to be refresed, no need for python
#    return {'ng': ng, "file": message}
    
    
    
@bottle.post('/crons')
def post_crons():
    tasks = []
    mapping = {}
    data = bottle.request.POST
    for k, v in data.items():
        if k.startswith('cron_') or k.startswith('file_'):
            k, i = k.split('_')
            task = mapping.setdefault(i, {})
            if k == 'file':
                v = os.path.join(upload_dir, v)
            task[k] = v
    tasks.extend([v for k, v in sorted(mapping.items())])
    if data.get('file'):
        tasks.append({'cron': data.get('cron'),
                      'file': os.path.join(upload_dir, data.get('file'))})
    crontab = Crontab(printer, upload_dir=upload_dir)
    crontab.write(tasks)
    bottle.redirect('/crons')


@bottle.get('/api/files')
def files():
    data = []
    for filename in sorted(glob.glob(os.path.join(upload_dir, '*.gcode'))):
        basename = os.path.basename(filename)
        data.append(dict(
            name=basename,
            print_url='/api/print/' + basename,
        ))
    return dict(files=data)


@bottle.get('/api/print/:filename')
def print_file(filename=None):
    cmd = [printer, os.path.join(upload_dir, filename)]
    p = subprocess.Popen(cmd) #, close_fds=True)
    time.sleep(1)
    data = call_client('jobs')
    if p.poll() is None:
        # process working
        return dict(success=True, result=data, prntr=printer)
    else:
        return dict(success=False, result=data)


@bottle.put('/upload')
def upload():
    fd = bottle.request.environ['wsgi.input']
    clength = bottle.request.content_length
    length = 0
    filename = fdout = None
    line = '-'
    while not line.startswith('------'):
        line = fd.readline()
        length += len(line)
        if length >= clength:
            bottle.abort(400)
    boundary = len(line) + 2
    while not line.startswith('Content-Disposition'):
        line = fd.readline()
        length += len(line)
        if length >= clength:
            bottle.abort(400)

    filename = line.split('filename=')[1].strip().strip('"')
    filename = os.path.basename(filename)
    filename = filename.replace(' ', '_')

    if not filename.endswith('.gcode'):
        bottle.abort(400)

    while line != '\r\n':
        line = fd.readline()
        length += len(line)
        if length >= clength:
            return dict(result=dict(files=['Invalid upload']))

    with open(os.path.join(upload_dir, filename), 'wb') as fdout:
        for line in fd:
            length += len(line)
            if length + boundary >= clength:
                break
            fdout.write(line)
    return files()


@bottle.route('/static/<path:path>')
def static(path):
    return bottle.static_file(path, static_root)


def make_app():
    bottle.debug(mode=False)
    return bottle.default_app()
