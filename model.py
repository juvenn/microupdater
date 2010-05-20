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
  # Class constant. PuSH verify_token 
  TOKEN = "SSBMb3ZlIFlvdSwgSm91bGUK" 

  title = db.StringProperty(required=True)
  topic = db.LinkProperty(required=True)
  # Feed's unique identifier
  uid = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  featured = db.BooleanProperty(default=False)
  logo = db.LinkProperty(required=True)
  # Subscribe status
  status = db.StringProperty(default="unsubscribed",
      choices = ["subscribing",
	         "subscribed",
		 "unsubscribing",
		 "unsubscribed"])

  twitter = db.StringProperty()
  friendfeed = db.StringProperty()

  @property
  def latest_entry(self):
    q = self.entry_set.order("-updated")
    return q.get()
    
class Entry(db.Model):
  author = db.StringProperty()
  title = db.StringProperty(required=True)
  # Entry's unique identifier 
  uid = db.StringProperty(required=True)
  link = db.LinkProperty(required=True)
  content = db.TextProperty()
  updated = db.DateTimeProperty(required=True)
  channel = db.ReferenceProperty(Channel,required=True)

  @property
  def date(self):
    return self.updated.date()

  @staticmethod
  def cleanup(days=30):
    """Cleanup datastore.
    Cleaup by delete old entries, default to updated 30 days ago
    """
    outdate = datetime.utcnow() - timedelta(days)
    entry_query = Entry.all().order("updated").filter("updated <=",outdate)
    entries = entry_query.fetch(100)
    db.delete(entries)
    logging.info("Entries updated before %s were succeesfully deleted." %
	outdate.isoformat())


