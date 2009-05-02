#!/usr/bin/env python
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#


"""Remote Data Sync"""

import logging
from datetime import datetime
from google.appengine.ext import db
from google.appengine.api import urlfetch

# Universal Feedparser 
# Copyright (c) Mark Pilgrim
# http://feedparser.org
import feedparser
from mudel import Entry, Channel

class Updater(db.Model):
  url = db.LinkProperty(required=True)
  updatable = db.BooleanProperty(default=True)
  etag = db.StringProperty()
  last_modified = db.StringProperty()
  created_at = db.DateTimeProperty(auto_now_add = True)

  @property
  def last_fetched(self):
    e = Entry.all().order("-published").get()
    if e: return e.published
    # Gurantee an initial datetime if no entries 
    else: return datetime(2009,4,23)

  def fetch(self):
    """Fetch data"""
    header = {}
    header["If-None-Match"] = self.etag
    header["If-Modified-Since"] = self.last_modified
    header["User-Agent"] = "Microupdater/0.5 http://microupdater.com"
    try:
      resp = urlfetch.fetch(url=self.url, headers=header)
    except Error, e:
      logging.warning("%s urlfetch failed. %s" % (self.url, e))
      return

    if resp.status_code == 202:
      self._extract(resp.content)
    elif resp.status_code == 301:
      redirect_url = resp.header.get("location")
      if redirect_url: 
	self.url = redirect_url
	logging.warning("%s permanetly redirect, changed to %s." % (self.url, redirect_url))
      else: logging.warning("%s permanetly redirected." % self.url)
    elif resp.status_code == 410:
      self.updatable = False
      logging.warning("%s permanetly removed." % self.url)
    else: logging.error("urlfetch response status code: %s" % resp.status_code)

    self.etag = resp.headers.get("etag")
    self.last_modified = resp.headers.get("last-modified")
    self.put()
    return

  def _extract(self, data):
    """Parse the data and put into datastore."""
    pa = feedparser.parse(data)
    if pa.feed:
      tt = self.last_fetched.isoformat()
      entries = [e for e in pa.entries if e.published > tt]
      if entries:
	for e in entries:
	  chnl = Channel.filter("reader_id =", e.source.id).get()
	  if not chnl:
	    chnl = Channel(title=e.source.title,
		link=e.source.link,
		reader_id=e.source.id
		)
	    chnl.put()

	  if e.haskey("content"): content = e.content[0].value
	  else: content = e.summary
	  t = e.published_parsed
	  pub_at = datetime(t[0],t[1],t[2],t[3],t[4],t[5])
	  ent = Entry(title=e.title,
	      link=e.link,
	      summary=content,
	      author=e.author,
	      published=pub_at,
	      reader_id=e.id,
	      channel=chnl
	      ) 
	  ent.put()
