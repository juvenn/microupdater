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
    producer = db.StringProperty(required=True)
    description = db.TextProperty()

    # Feed and its update status.
    title = db.StringProperty()
    link = db.LinkProperty(required=True)
    # The last update time.
    updated = db.DateTimeProperty()
    # The last fetch time.
    last_fetch = db.DateTimeProperty()
    etag = db.StringProperty()
    last_modified = db.StringProperty()
    # Only approved channel get updates.
    is_approved = db.BooleanProperty(default=False)

    def initialize(self):
      # Check if it's already in db.
      #if not Channel.all().filter("link =", self.link):
      re = urlfetch.fetch(url=self.link)
      if re.status_code == 200:
	pa = feedparser.parse(re.content)
	if pa.feed.has_key("publisher") and not self.producer:
	  self.producer = pa.feed.publisher
	self.title = pa.feed.title
	self.updated = self.last_fetch = datetime(2008, 11, 01)
	self.etag = re.headers.get("etag")
	self.last_modified = re.headers.get("last-modified")
      self.put()

class Entry(db.Model):
    author = db.StringProperty()
    title = db.StringProperty(required=True)
    link = db.LinkProperty(required=True)
    # Content of the entry.
    summary = db.TextProperty()
    # The last updated time of the entry.
    updated = db.DateTimeProperty(required=True)
    channel = db.ReferenceProperty(reference_class=Channel, required=True)

    # Clear outdated entries.
    def clear(chnl, clear_td=timedelta(30, 0, 0)):
	outdated_dt = datetime.utcnow() - clear_td
	for ent in chnl.entry_set:
	    if ent.updated <= outdated_dt:
		ent.delete()
