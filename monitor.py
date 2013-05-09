#!/usr/bin/env python

"""A working (and used!) example of using pyinotify to trigger data reduction.

A multiprocessing pool of thread workers is used to perform the reduction in
an asynchronous and parallel fashion.
"""
import sys
import multiprocessing
import logging, logging.handlers
import os
import optparse
from functools import partial
import pyinotify
from autocrunch.watch_handlers import RsyncNewFileHandler
import ami
import drivecasa

logger = logging.getLogger()

class options():
    """Dummy class serving as a placeholder for optparse handling."""
    ami = "/opt/ami"
    casa = '/opt/soft/builds/casapy-active'
    output_dir = "/home/usename/autocrunch_results"
#    log_dir = '/tmp/autocruncher'
    log_dir = output_dir
    nthreads = 4

def main(options):
    """Define processing logic and fire up the watcher"""
    watchdir = os.path.join(options.ami, 'LA/data')
    pool = multiprocessing.Pool(options.nthreads)

#    def simply_process_rawfile(file_path):
#        summary = process_rawfile(file_path)
#        processed_callback(summary)
    def asynchronously_process_rawfile(file_path, mp_pool):
        """Wrapper function that runs 'process_rawfile' asynchronously via pool"""
        mp_pool.apply_async(process_rawfile,
              [file_path, options.ami, options.casa, options.output_dir],
              callback=processed_callback)

    bound_asyncprocessor = partial(asynchronously_process_rawfile, mp_pool=pool)
    handler = RsyncNewFileHandler(nthreads=options.nthreads,
                                  file_predicate=is_rawfile,
                                  file_processor=bound_asyncprocessor)
    wm = pyinotify.WatchManager()
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(watchdir, handler.mask, rec=True)
    log_preamble(options, watchdir)
    notifier.loop()
    return 0


def is_rawfile(filename):
    """Predicate function for identifying incoming AMI data"""
    if '.raw' in filename:
        return True
    return False

def process_rawfile(filename, ami_dir, casa_dir, output_dir):
    """A data reduction subroutine (specific to user's application)."""
    rawfile = os.path.basename(filename)
    reduce = ami.Reduce(ami_dir)
    groupname = rawfile.split('-')[0]
    group_dir = os.path.join(output_dir, groupname)
    ami_output_dir = os.path.join(group_dir, 'ami')
    try:
        obs_info = ami.process_rawfile(rawfile, ami_output_dir, reduce)
        drivecasa.process_observation(obs_info, group_dir, casa_dir)
    except (IOError, ValueError) as e:
        error_message = ("Hit exception reducing file: %s, exception reads:\n%s\n"
                         % (rawfile, e))
        return error_message

    return "Successfully processed " + filename

def processed_callback(summary):
    """Used to return the 'job complete' log message in the master thread."""
    logger.info('*** Job complete: ' + summary)


def log_preamble(options, watchdir):
    logger.info("***********")
    logger.info('Watching %s', watchdir)
    logger.info('Ami dir %s', options.ami)
    logger.info('Casa dir %s', options.casa)
    logger.info('Ouput dir %s', options.output_dir)
    logger.info('Log dir %s', options.log_dir)
    logger.info("***********")

def setup_logging(options):
    """Set up basic (INFO level) and debug logfiles

    These should list successful reductions, and any errors encountered.
    We also copy the basic log to STDOUT, but it is expected that
    the monitor script will be daemonised / run in a screen in the background.
    """
    if not os.path.isdir(options.log_dir):
        os.makedirs(options.log_dir)
    log_filename = os.path.join(options.log_dir, 'autocruncher_log')
    date_fmt = "%a %d %H:%M:%S"
    std_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s', date_fmt)
    debug_formatter = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s', date_fmt)

    fhandler = logging.handlers.RotatingFileHandler(log_filename,
                            maxBytes=5e5, backupCount=10)
    fhandler.setFormatter(std_formatter)
    fhandler.setLevel(logging.INFO)
    dhandler = logging.handlers.RotatingFileHandler(log_filename + '.debug',
                            maxBytes=5e5, backupCount=10)
    dhandler.setFormatter(debug_formatter)
    dhandler.setLevel(logging.DEBUG)

    shandler = logging.StreamHandler()
    shandler.setFormatter(std_formatter)
    shandler.setLevel(logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fhandler)
    logger.addHandler(shandler)
    logger.addHandler(dhandler)


if __name__ == '__main__':
    setup_logging(options)
    sys.exit(main(options))
