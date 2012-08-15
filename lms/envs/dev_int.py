"""
This enables use of course listings by subdomain. To see it in action, point the
following domains to 127.0.0.1 in your /etc/hosts file:

  berkeley.dev
  harvard.dev
  mit.dev

Note that OS X has a bug where using *.local domains is excruciatingly slow, so
use *.dev domains instead for local testing.
"""
from .dev import *

MITX_FEATURES['SUBDOMAIN_COURSE_LISTINGS'] = True

COURSE_LISTINGS = {
    'default' : ['BerkeleyX/CS169.1x/2012_Fall',
                 'BerkeleyX/CS188.1x/2012_Fall',
                 'HarvardX/CS50x/2012',
                 'HarvardX/PH207x/2012_Fall'
                 'MITx/3.091x/2012_Fall',
                 'MITx/6.002x/2012_Fall',
                 'MITx/6.00x/2012_Fall'],

    'berkeley': ['BerkeleyX/CS169.1x/2012_Fall',
                 'BerkeleyX/CS188.1x/2012_Fall'],

    'harvard' : ['HarvardX/CS50x/2012'],

    'mit'     : ['MITx/3.091x/2012_Fall',
                 'MITx/6.00x/2012_Fall']
}
