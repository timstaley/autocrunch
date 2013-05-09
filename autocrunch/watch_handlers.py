import os
import pyinotify
import logging
logger = logging.getLogger(__name__)

class RsyncNewFileHandler(pyinotify.ProcessEvent):
    """Identifies new rsync'ed files and passes their path for processing.

    rsync creates temporary files with a `.` prefix and random 6 letter suffix,
    then renames these to the original filename when the transfer is complete.
    To reliably catch (only) new transfers while coping with this file-shuffling,
    we must do a little bit of tedious file tracking, using
    the internal dict `tempfiles`.
    Note we only track those files satisfying the condition
    ``file_predicate(basename)==True``.

    """
    def my_init(self, nthreads, file_predicate, file_processor):
        self.mask = pyinotify.IN_CREATE | pyinotify.IN_MOVED_TO
        self.tempfiles = {}
        self.predicate = file_predicate
        self.process = file_processor

    def process_IN_CREATE(self, event):
        original_filename = os.path.splitext(event.name[1:])[0]
        if self.predicate(original_filename):
            logger.debug("Transfer started, tempfile at:\n\t%s\n",
                         event.pathname)
            self.tempfiles[original_filename] = event.pathname

    def process_IN_MOVED_TO(self, event):
        #Now rsync has renamed the file to drop the temporary suffix.
        #NB event.name == basename(event.pathname) AFAICT
        if event.name in self.tempfiles:
            self.tempfiles.pop(event.name)
            logger.info('Sending for processing: %s', event.pathname)
            self.process(event.pathname)
