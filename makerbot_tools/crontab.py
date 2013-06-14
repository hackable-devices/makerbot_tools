# -*- coding: utf-8 -*-
import subprocess
import tempfile
import os


class Crontab(object):

    def __init__(self, printer, upload_dir=None):
        self.printer = printer
        self.upload_dir = upload_dir
        self.tasks = []

    def read(self):
        crontab = subprocess.check_output(['crontab', '-l'])
        for line in crontab.split('\n'):
            line = line.strip()
            if not line or self.printer not in line:
                continue
            line = line.split(' ', 5)
            task = line.pop()
            filename = task.split(' ')[1]
            self.tasks.append([' '.join(line), filename])

    def write(self, tasks):
        fd = tempfile.NamedTemporaryFile(mode='w')
        fd.write('# Do not change this crontab. Use conveyor-ui instead\n\n')
        for t in tasks:
            t['printer'] = self.printer
            fd.write('%(cron)s %(printer)s %(file)s\n' % t)
        fd.write('\n')
        fd.flush()
        subprocess.check_output(['crontab', fd.name])
        fd.close()

    def __iter__(self):
        return enumerate(self.tasks)

    def select(self, filename, filenames):
        filename = os.path.basename(filename)
        options = []
        for n in filenames:
            options.append((n, filename == n))
        return options
