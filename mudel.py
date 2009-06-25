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
  logo = db.LinkProperty(default=None)
  created_at = db.DateTimeProperty(auto_now_add=True)
  reader_id = db.StringProperty(required=True)

  blog = db.LinkProperty(required=True)
  status = db.LinkProperty()
  twitter = db.StringProperty()
  friendfeed = db.StringProperty()

  @property
  def latest_entry(self):
    q = self.entry_set.order("-published")
    return q.get()
    
class Entry(db.Model):
  author = db.StringProperty()
  title = db.StringProperty(required=True)
  link = db.LinkProperty(required=True)
  summary = db.TextProperty()
  published = db.DateTimeProperty(required=True)
  reader_id = db.StringProperty(required=True)
  channel = db.ReferenceProperty(Channel,required=True)

  @property
  def pub_date(self):
    return self.published.date()

  @classmethod
  def cleanup(td=timedelta(30, 0, 0)):
    """Cleanup datastore.
    Cleaup by delete old entries, default to published 30 days ago
    """
    outdate = datetime.utcnow() - td
    entry_query = Entry.all.order("published").filter("published <=",outdate)
    entries = entry_query.fetch(1000)
    for e in entries: 
      e.delete()
    logging.info("Entries published before %s were succeesfully deleted." %
	outdate.isoformat())

class Featured(db.Model):
  title = db.StringProperty()
  start = db.DateTimeProperty()
  end = db.DateTimeProperty()
  enabled = db.BooleanProperty()
  channel = db.ReferenceProperty(Channel)
  created_at = db.DateTimeProperty(auto_now_add=True)


