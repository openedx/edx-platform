import logging
import datetime
import os
from os.path import join as pjoin


log = logging.getLogger('doto')
log.setLevel(logging.DEBUG)

try:
  os.path.expanduser('~')
  expanduser = os.path.expanduser
except (AttributeError, ImportError):
  # This is probably running on App Engine.
  expanduser = (lambda x: x)

DOTO_DIR = pjoin(expanduser('~'),'.doto')
DOTO_LOG_DIR = pjoin(DOTO_DIR,'doto-logs')
now = datetime.datetime.utcnow().strftime('%Y-%m-%d')


if not os.path.exists(DOTO_LOG_DIR):
    os.makedirs(DOTO_LOG_DIR)

DEBUG_FILE = pjoin(DOTO_LOG_DIR, 'doto-%s.log' % (now))

#create file handler which logs even debug messages
fh = logging.FileHandler(DEBUG_FILE)
fh.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter and add it to the handlers
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(file_formatter)

console_formatter = logging.Formatter('>>> %(message)s')

ch.setFormatter(console_formatter)

# add the handlers to the logger
log.addHandler(fh)
log.addHandler(ch)
