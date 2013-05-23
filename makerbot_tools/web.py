# -*- coding: utf-8 -*-
import subprocess
import bottle
import json
import glob
import os

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
print(client)

bottle.TEMPLATE_PATH.append(
    os.path.join(dirname, 'views')
)
static_root = os.path.join(dirname, 'static')


def call_client(*args):
    try:
        data = subprocess.check_output([client] + list(args))
    except subprocess.CalledProcessError:
        bottle.abort(500)
    if data.strip():
        data = dict(status=0, result=json.loads(data))
    else:
        data = dict(status=1)
    return data


def client_response(*args):
    def req():
        return call_client(*args)
    return req


@bottle.route('/')
@bottle.view('index')
def index():
    return {}


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


bottle.route('/api/printers', callback=client_response('printers'))
bottle.route('/api/jobs', callback=client_response('jobs'))


@bottle.route('/api/print/:filename')
def print_file():
    # need to interact with client
    return {}


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
