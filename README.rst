==========
autocrunch
==========
A utility script which illustrates use of 
`pyinotify <https://github.com/seb-m/pyinotify>`_ 
to detect and process files transferred into a particular folder.

Mostly very specific to my application, but ``watch_handlers.RsyncNewFileHandler``
may be of use to others. Feel free to cut'n'paste.

Processing is performed asynchronously and with N threads. Which is nice.


Installation
------------

 git clone git://github.com/timstaley/autocrunch.git

 cd autocrunch

 pip install .
 
