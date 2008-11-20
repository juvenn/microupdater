#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Update engine of Microupdater

Traverse all channels, check remote server for any updates, fetch from the channel if updates available, parse it by feedparser, and put optional parsednodes to db.

"""

# Import from standard Python library.
from datetime import datetime, timedelta

# Import from user-defined modules.
from mudel import Channel, Entry, Featured

# URLFetch timedelta(days, fracseconds, fracmicroseconds). 
# Intended urlfetch.fetch() will be ignored within a FETCH_TD cycle.
FETCH_TD = timedelta(0, 300, 0) 

def sync():
  for chnl in Channel.all().filter("updatable =", True):
    tmnow = datetime.utcnow()
    if tmnow-chnl.last_fetch > FETCH_TD:
      chnl.getupdates()
    chnl.last_fetch = tmnow
    chnl.put()
