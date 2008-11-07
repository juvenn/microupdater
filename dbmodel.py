#!/usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Customized db schema for Microupdater."""

from datetime import datetime, timedelta
from google.appengine.ext import db
from google.appengine.api import urlfetch

import feedparser

class Channel(db.Model):
    # About team and products. 
    producer = db.StringProperty()
    description = db.TextProperty(default=None)

    # Feed and its update status.
    title = db.StringProperty()
    link = db.LinkProperty(required=True)
    # The last update time.
    updated = db.DateTimeProperty(auto_now=True)
    # The last fetch time.
    last_fetch = db.DateTimeProperty()
    etag = db.StringProperty()
    last_modified = db.StringProperty()
    # Only approved channel get updates.
    is_approved = db.BooleanProperty(default=True)

    def initialize(self):
      # Validate url and check if it's already in db.
      if not Channel.all().filter("link =", self.url):
	re = urlfetch.fetch(self.link)
	if re.status_code == 200:
	  pa = feedparser.parse(re.content)
	  if not self.producer:
	    self.producer = pa.feed.publisher
	  self.title = pa.feed.title
	  self.updated = tmnow = datetime.utcnow()
	  self.last_fetch = tmnow
	  if re.headers.has_key["ETag"]: self.etag = re.headers["ETag"]
	  if re.headers.has_key["Last-Modified"]: 
	    self.last_modified = re.headers["Last-Modified"]

class Entry(db.Model):
    author = db.StringProperty()
    title = db.StringProperty()
    link = db.LinkProperty()
    # Truncated content of the entry, instead of original entry summary.
    summary = db.TextProperty()
    # The last updated time of the entry.
    updated = db.DateTimeProperty()
    channel = db.ReferenceProperty(Channel)

    # Clear outdated entries.
    def clear(chnl, clear_td):
	outdated_dt = datetime.utcnow() - clear_td
	for ent in chnl.entry_set:
	    if ent.updated <= outdated_dt:
		ent.delete()
