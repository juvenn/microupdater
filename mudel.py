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
  blog = db.LinkProperty(required=True)
  created_at = db.DateTimeProperty(auto_now_add=True)
  featured = db.BooleanProperty(default=False)
  logo = db.LinkProperty(required=True)
  #subscribe status
  status = db.StringProperty(default="unsubscribed",
      choices = ["subscribing",
	         "subscribed",
		 "unsubscribing",
		 "unsubscribed"])

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
  channel = db.ReferenceProperty(Channel,required=True)

  @property
  def pub_date(self):
    return self.published.date()

  @staticmethod
  def cleanup(days=30):
    """Cleanup datastore.
    Cleaup by delete old entries, default to published 30 days ago
    """
    outdate = datetime.utcnow() - timedelta(days)
    entry_query = Entry.all().order("published").filter("published <=",outdate)
    entries = entry_query.fetch(100)
    db.delete(entries)
    logging.info("Entries published before %s were succeesfully deleted." %
	outdate.isoformat())


# Deprecated model
class Featured(db.Model):
  title = db.StringProperty()
  start = db.DateTimeProperty()
  end = db.DateTimeProperty()
  enabled = db.BooleanProperty()
  channel = db.ReferenceProperty(Channel)
  created_at = db.DateTimeProperty(auto_now_add=True)


