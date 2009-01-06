#! /usr/bin/env python
#
# Copyright (c) 2008 Juvenn Woo.
# http://twitter.com/juvenn
#

"""Customized db schema for Microupdater."""

from datetime import datetime, timedelta
import logging
import re

from google.appengine.ext import db
from google.appengine.api import urlfetch

# Universal Feed Parser. Copyright (c) Mark Pilgrim.
# Visit http://feedparser.org
import feedparser
from helper import timetuple2datetime

class Feed(db.Model):
  url = db.LinkProperty(required=True)
  updated = db.DateTimeProperty()
  created_at = db.DateTimeProperty(auto_now_add=True)
  # Update status.
  updatable = db.BooleanProperty(default=True)
  etag = db.StringProperty()
  last_modified = db.StringProperty()
  last_fetch = db.DateTimeProperty()

  def get_updates(self):
    """Update self

    Returns:
      self, if update succeeded.
      False, if failed.
    """
    h = {}
    if self.etag: h["If-None-Match"] = self.etag
    if self.last_modified: h["If-Modified-Since"] = self.last_modified
    try:
      rp = urlfetch.fetch(url=self.url, headers=h)
      self.last_fetch = datetime.utcnow()
    except:
      logging.erro("%s urlfetch failed.", self.url)
      return False

    if rp.status_code == 200:
      try:
	pa = feedparser.parse(rp.content)
      except:
	logging.warning("Feedparser failed to parse %s.", self.url)
	return False

      if pa.feed:
	upto = timetuple2datetime(pa.feed.updated_parsed)
	if upto > self.updated:
	  tt = self.updated.utctimetuple()
	  up_entries = [e for e in pa.entries if e.updated_parsed > tt]
	  for e in up_entries:
	    ent = Entry(author=e.get("author"),
		title=e.title,
		url=e.link,
		channel_title=e.source.title,
		channel_url=db.Link(e.source.link),
		updated=timetuple2datetime(e.updated_parsed))
	    if e.has_key("content"):
	      ent.content = e.content[0].value
	    else: ent.content = e.get("summary")
	    mch = re.search('src="(http.*\.(png|gif|jpg))"', ent.content)
	    if mch: ent.imgsrc = db.Link(mch.group(1))
	    ent.put()
	  self.updated = upto
	  self.etag = rp.headers.get("etag")
	  self.last_modified = rp.headers.get("last-modified")
	  self.put()
	  return self

    elif rp.status_code == 410:
      self.updatable = False
      self.put()
      logging.warning("%s permanetly removed from the server.", self.url)
    return False


    
class Entry(db.Model):
  author = db.StringProperty()
  title = db.StringProperty(required=True)
  url = db.LinkProperty(required=True)
  content = db.TextProperty()
  imgsrc = db.LinkProperty()
  updated = db.DateTimeProperty()

  channel_title = db.StringProperty()
  channel_url = db.LinkProperty()

  # Clear outdated entries, default saving for 30 days.
  def clear(td=timedelta(30, 0, 0)):
    """clear()
    Clear outdated entries, i.e. default 30 days since updated.
    """
    outdated_dt = datetime.utcnow() - td
    for ent in Entry.all().order('updated'):
      if ent.updated <= outdated_dt: ent.delete()
      logging.info("Entries updated before %s were cleared.",
	  outdated_dt.strftime("%c"))


