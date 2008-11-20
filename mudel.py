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

# Universal Feed Parser. Copyright (c) Mark Pilgrim.
# Visit http://feedparser.org
import feedparser
from helper import timetuple2datetime

class Channel(db.Model):
    # About channel.
    producer = db.StringProperty(verbose_name='Producer',
	default=None)
    url = db.LinkProperty(verbose_name='Product Blog',
	required=True)
    tags = db.ListProperty(item_type=db.Category, 
	verbose_name='Tags')
    
    # Channel update status.
    updatable = db.BooleanProperty(default=False)
    updated = db.DateTimeProperty(default=None)
    last_fetch = db.DateTimeProperty(default=None)
    etag = db.StringProperty(default=None)
    last_modified = db.StringProperty(default=None)

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
	    self.updated = self.last_fetch = datetime.now()
	    self.etag = re.headers.get("etag")
	    self.last_modified = re.headers.get("last-modified")
            self.put()
	    return self

    def getupdates(self):
      # Construct headers.
      h = {}
      if self.etag: h["If-None-Match"] = self.etag
      if self.last_modified:
	h["If-Modified-Since"] = self.last_modified

      try:
	re = urlfetch.fetch(url=self.url, headers=h)
      except:
	logging.erro("%s urlfetch failed.", self.url)
      else:
	if re.status_code == 200:
	  pa = feedparser.parse(re.contetn)
	  if pa.feed:
	    # Get latest update time.
	    try:
	      updatetime = timetuple2datetime(pa.feed.updated_parsed)
	    except:
	      # Get updatetime from latest entry's updated.
	      dts = [e.updated_parsed for e in pa.entries]
	      dts.sort().reverse()
	      updatetime = timetuple2datetime(dts[0])
	    
	    if updatetime > self.updated:
	      # Extract updated entries.
	      tt = self.updated.utctimetuple()
	      updated_entries = [e for e in pa.entries \
		  if e.updated_parsed > tt]
	      # Updated the Entry table.
	      for e in updated_entries:
		e_updatetime = timetuple2datetime(e.updated_parsed)
		ent = Entry(author=e.get("author"),
		    title=e.title,
		    link=e.link,
		    updated=e_updatetime,
		    channel=self)
		# Get entry summary.
		if e.has_key("content"):
		  ent.summary = db.Text(e.content[0].value)
		elif e.has_key("summary"): ent.summary = db.Text(e.summary)
		ent.put()
	    self.updated = updatetime
	    self.etag = re.headers.get("etag")
	    self.last_modified = re.headers.get("last-modified")

	# For permanetly removed link, stop to update.
	elif re.status_code == 410:
	  self.updatable = False
	  logging.warning("%s permanetly removed from the server.", self.url)
	self.put()

    
class Entry(db.Model):
    title = db.StringProperty(required=True)
    link = db.LinkProperty(required=True)
    summary = db.TextProperty(default=None)
    imgsrc = db.LinkProperty(default=None)
    updated = db.DateTimeProperty(default=None)

    channel = db.ReferenceProperty(reference_class=Channel,
	collection_name='entries',
	required=True)

    # Clear outdated entries, default saving for 30 days.
    def clear(td=timedelta(30, 0, 0)):
        """clear()

	Clear outdated entries, i.e. default 30 days since updated.
	"""
	outdated_dt = datetime.utcnow() - td
	for ent in Entry.all().order('updated'):
	    if ent.updated <= outdated_dt:
		ent.delete()
        logging.info("Entries updated before %s were cleared.",
	    outdated_dt.strftime("%c"))


class Featured(db.Model):
  """Featured status

  For channels featured on top or side. Includes start and end of being
  featured, exclusive featured on top or not, etc.
  """
  channel = db.ReferenceProperty(reference_class=Channel, required=True)
  exclusive = db.BooleanProperty(default=False)

  # Featured time.
  start_dt = db.DateTimeProperty(default=None)
  end_dt = db.DateTimeProperty(default=None)

  @property
  def latest_entry(self):
    return self.channel.entires.order('-updated').get()
