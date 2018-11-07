import logging
import os
import zipfile


logger = logging.getLogger(__name__)

class ZIPFile(object):

    def __init__(self, path, zipfilename):
        self.path = path
        self.zipfilename = zipfilename

    def extract_all(self):
        logger.info("Extracting file(s) from %s/%s ..." % (self.path, self.zipfilename))

        with zipfile.ZipFile(self.path + "/" + self.zipfilename, 'r') as zip_ref:
            zip_ref.extractall(os.path.dirname(self.path + "/" + self.zipfilename))
