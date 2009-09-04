#!/usr/bin/env python
#
# Copyright (c) 2009 Juvenn Woo.
# http://twitter.com/juvenn.
#


"""Remote Data Sync Module"""

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
    # Gaurantee an initial datetime if no entries 
    else: return datetime(2009,4,23)

  def sync(self):
    """Synchronization
    Returns:
      True, if succeeded;
      False, if not.
    """
    data = self._fetch()
    if data:
      entries = self._extract(data)
      if entries:
	if self._putd(entries): return True
    return False


  def _fetch(self):
    """Fetch Data
    Returns:
      fetched data body, if succeeded;
      None, if not.
    """
    h = {}
    h["If-None-Match"] = self.etag
    h["If-Modified-Since"] = self.last_modified
    h["User-Agent"] = "Microupdater/0.5 http://microupdater.com"
    try:
      resp = urlfetch.fetch(url=self.url, headers=h)
    except urlfetch.Error:
      logging.warning("%s urlfetch failed" % self.url)
      raise

    if resp.status_code == 200:
      return resp.content
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
    return None

  def _extract(self, data):
    """Extract New Entries
    Returns:
      New entries, if there are;
      None, if not.
    """
    pa = feedparser.parse(data)
    if pa.feed:
      # "Z" of UTC timezone
      tt = self.last_fetched.isoformat() + "Z"
      entries = [e for e in pa.entries if e.published > tt]
      return entries

  def _putd(self, entries):
    """Put Entities
    Returns:
      True, if succeeded;
      False, if not.
    """
    if not entries: return False
    entries_to_put = []
    channels_to_put = []
    for e in entries:
      if Entry.all().filter("reader_id =", e.id).get(): break
      chnl = Channel.all().filter("reader_id =", e.source.id).get()
      if not chnl:
	fo
	src_title = e.source.title.split(" - ")[0]
	chnl = Channel(key_name=e.source.id,
	               title=src_title,
		       blog=e.source.link,
		       reader_id=e.source.id)
	chnl_key = db.Key.from_path('Channel', e.source.id)
	channels_to_put.append(chnl)
      if e.has_key("content"): content = e.content[0].value
      else: content = e.summary
      t = e.published_parsed
      pub_at = datetime(t[0],t[1],t[2],t[3],t[4],t[5])
      if e.author == "(author unknown)": e.author = None
      ent = Entry(title=e.title,
	          link=e.link,
	          summary=content,
	          author=e.author,
	          published=pub_at,
	          reader_id=e.id,
	          channel=chnl_key) 
      entities.append(ent)
    db.put(entities)
    return True

