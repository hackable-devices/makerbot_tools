Installation
=============

Debian packages::

    # aptitude install git-core

If you do not already have python2.7 installed::

    # aptitude install python2.7

With ssh git::

    $ git clone git://github.com/hackable-devices/makerbot_tools.git
    $ cd makerbot_tools

With git+ssh::

    $ git clone git@github.com:hackable-devices/makerbot_tools.git
    $ cd makerbot_tools

With wget::

    $ url=https://github.com/hackable-devices/makerbot_tools/archive/master.tar.gz
    $ wget --no-check-certificate -O- $url | tar xzvf -
    $ cd makerbot_tools-master

Then bootsrap the project::

    $ python bootstrap.py
    $ bin/buildout

Usage
=====

Launch the server::

    $ sudo bin/conveyor-server [start|stop]

Launch the webserver::

    $ ./server.py

Validate and Print something::

    $ bin/print file.gcode

Print something directly::

    $ bin/s3b_print file.gcode

Print useful informations::

    $ bin/conveyor-client printers
    $ bin/conveyor-client jobs
