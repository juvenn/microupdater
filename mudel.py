#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Data Model"""

import logging
from datetime import datetime, timedelta
from google.appengine.ext import db

class Channel(db.Model):
  title = db.StringProperty(required=True)
  link = db.LinkProperty(required=True)
  created_at = db.DateTimeProperty(auto_now_add=True)
  reader_id = db.StringProperty(required=True)

    
class Entry(db.Model):
  author = db.StringProperty()
  title = db.StringProperty(required=True)
  link = db.LinkProperty(required=True)
  summary = db.TextProperty(required=True)
  published = db.DateTimeProperty(required=True)
  reader_id = db.StringProperty(required=True)
  channel = db.ReferenceProperty(Channel,required=True)


  def cleanup(td=timedelta(30, 0, 0)):
    """Cleanup datastore.
    Cleaup by delete old entries, default to published 30 days ago
    """
    outdate = datetime.utcnow() - td
    entry_query = Entry.all.order("published").filter("published <=",outdate)
    entries = entry_query.fetch(1000)
    for e in entries: 
      e.delete()
    logging.info("Entries published before %s were succeesfully deleted.",
	outdate.isoformat())

