#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Customized db schema for Microupdater."""

from datetime import datetime, timedelta
import logging
from google.appengine.ext import db
from google.appengine.api import urlfetch

import feedparser

class Channel(db.Model):
    # About team. 
    producer = db.StringProperty()
    location = db.PostalAddressProperty()

    url = db.LinkProperty(required=True)
    img_src = db.LinkProperty()
    # The last update time.
    updated = db.DateTimeProperty()
    # The last fetch time.
    last_fetch = db.DateTimeProperty()
    etag = db.StringProperty()
    last_modified = db.StringProperty()

    # Only approved channel get updates.
    is_approved = db.BooleanProperty()
    # Featured or not
    is_featured =db.BooleanProperty()

    # Categories: web, desktop, mobile
    is_web = db.BooleanProperty()
    is_desktop = db.BooleanProperty()
    is_mobile = db.BooleanProperty()

    def initialize(self):
      """initialize()

      Attempt to fetch the channel url, 
      get initial etag and last-modified value.

      Returns:
        The initialized entity, if succeeded.
      """
      try:
        re = urlfetch.fetch(url=self.url)
      except:
	raise
      else:
	if re.status_code == 200:
	  pa = feedparser.parse(re.content)
	  if pa.feed:
	    if not self.producer:
	      self.producer = pa.feed.get("publisher")
	    if not self.img_src:
	      self.img_src = pa.feed.image.get("href")
	    self.updated = self.last_fetch = datetime.now()
	    self.etag = re.headers.get("etag")
	    self.last_modified = re.headers.get("last-modified")
            self.put()
	    return self

class Entry(db.Model):
    title = db.StringProperty()
    link = db.LinkProperty()
    # Content of the entry.
    summary = db.TextProperty()
    img_src = db.LinkProperty()

    # The last updated time of the entry.
    updated = db.DateTimeProperty()
    # on_date = updated.date(), for template regroup.
    # e.g. 
    # {% regroup entries by on_date as group %}
    on_date = db.DateTimeProperty()

    channel = db.ReferenceProperty(reference_class=Channel)

    # Clear outdated entries, default saving for 30 days.
    def clear(clear_td=timedelta(30, 0, 0)):
        """clear()

	Clear outdated entries, i.e. default 30 days since updated.
	"""
	outdated_dt = datetime.utcnow() - clear_td
	for ent in Entry.all().order('updated'):
	    if ent.updated <= outdated_dt:
		ent.delete()
        logging.info("Entries updated before %s were cleared.",
	    outdated_dt.strftime("%c"))
